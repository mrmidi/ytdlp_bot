#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Ensure the script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Error: Please run this script as root (sudo)."
  exit 1
fi

PROJECT_DIR="$(pwd)"

echo "=== Let's Encrypt Certbot SSL Setup ==="
read -p "🌐 Enter your desired domain name (e.g., bot.yourdomain.com): " DOMAIN
read -p "📧 Enter email address for renewal notifications (default: admin@$DOMAIN): " EMAIL
EMAIL=${EMAIL:-"admin@$DOMAIN"}

if [ -z "$DOMAIN" ]; then
  echo "❌ Error: Domain name cannot be empty."
  exit 1
fi

# Install certbot if it is not installed
if ! command -v certbot &> /dev/null; then
  echo "📦 Certbot not found. Installing certbot via apt..."
  apt-get update
  apt-get install -y certbot lsof
else
  echo "✅ Certbot is already installed."
fi

# Check if port 80 is occupied and free it temporarily
WAS_NGINX_RUNNING=false
WAS_APACHE_RUNNING=false

if lsof -Pi :80 -sTCP:LISTEN -t >/dev/null ; then
  echo "⚠️ Port 80 is currently occupied. Freeing port 80..."
  
  if systemctl is-active --quiet nginx; then
    echo "🛑 Stopping Nginx..."
    systemctl stop nginx
    WAS_NGINX_RUNNING=true
  fi
  
  if systemctl is-active --quiet apache2; then
    echo "🛑 Stopping Apache..."
    systemctl stop apache2
    WAS_APACHE_RUNNING=true
  fi
  
  # Fail-safe check
  if lsof -Pi :80 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️ Warning: Port 80 is still occupied. Attempting to kill occupying process..."
    fuser -k 80/tcp || true
  fi
fi

echo "🔐 Requesting SSL certificate for $DOMAIN..."
# Request the standalone certificate
certbot certonly --standalone \
  -d "$DOMAIN" \
  --agree-tos \
  --email "$EMAIL" \
  --non-interactive

echo "📂 Creating certs directory at $PROJECT_DIR/certs..."
mkdir -p "$PROJECT_DIR/certs"

# Copy certificates to local project dir for Docker Compose mounting
echo "📋 Copying certificates to project folder..."
cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$PROJECT_DIR/certs/fullchain.pem"
cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$PROJECT_DIR/certs/privkey.pem"

# Make them readable by Docker containers
chmod 644 "$PROJECT_DIR/certs/fullchain.pem" "$PROJECT_DIR/certs/privkey.pem"

# Create a certbot deploy hook to automate renewal updates
echo "🤖 Creating automated renewal deploy hook..."
HOOK_PATH="/etc/letsencrypt/renewal-hooks/deploy/ytdlp_bot_deploy.sh"

cat <<EOF > "$HOOK_PATH"
#!/bin/bash
echo "🔄 Certbot renewal hook triggered for $DOMAIN."
cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$PROJECT_DIR/certs/fullchain.pem"
cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$PROJECT_DIR/certs/privkey.pem"
chmod 644 "$PROJECT_DIR/certs/fullchain.pem" "$PROJECT_DIR/certs/privkey.pem"

# Restart docker containers to load the new certificates
cd "$PROJECT_DIR"
if command -v docker-compose &> /dev/null; then
  docker-compose restart
elif command -v docker &> /dev/null; then
  docker compose restart
fi
echo "✅ Certificates copied and Docker containers restarted."
EOF

chmod +x "$HOOK_PATH"

# Restart web services if they were running before
if [ "$WAS_NGINX_RUNNING" = true ]; then
  echo "🚀 Restarting Nginx..."
  systemctl start nginx
fi

if [ "$WAS_APACHE_RUNNING" = true ]; then
  echo "🚀 Restarting Apache..."
  systemctl start apache2
fi

echo "========================================="
echo "🎉 Success! Certificates have been set up."
echo "🔗 Fullchain: $PROJECT_DIR/certs/fullchain.pem"
echo "🔑 Privkey:   $PROJECT_DIR/certs/privkey.pem"
echo "-----------------------------------------"
echo "💡 To mount these certificates in docker-compose.yml, add the following under volumes:"
echo "    volumes:"
echo "      - ./certs/fullchain.pem:/etc/certs/fullchain.pem:ro"
echo "      - ./certs/privkey.pem:/etc/certs/privkey.pem:ro"
echo "========================================="
