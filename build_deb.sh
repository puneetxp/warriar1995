#!/bin/bash
# Script to build a Debian package (.deb) for the Mental Wellness Tracker.

set -e

# Package metadata
PACKAGE_NAME="mental-wellness-tracker"
VERSION="1.0.0"
RELEASE="1"
ARCH="all"
BUILD_DIR="${PACKAGE_NAME}_${VERSION}-${RELEASE}_${ARCH}"

echo "Building Debian package structure..."

# Cleanup old build directory and deb package
rm -rf "$BUILD_DIR"
rm -f "${BUILD_DIR}.deb"

# Create directory structure
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/usr/share/$PACKAGE_NAME"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$BUILD_DIR/lib/systemd/system"
mkdir -p "$BUILD_DIR/etc/nginx/sites-available"

# 1. Copy application source files cleanly (excluding pycache)
cp main.py requirements.txt "$BUILD_DIR/usr/share/$PACKAGE_NAME/"
cp -r models routers security services utils "$BUILD_DIR/usr/share/$PACKAGE_NAME/"
find "$BUILD_DIR/usr/share/$PACKAGE_NAME" -type d -name "__pycache__" -exec rm -rf {} +

# 2. Create the executable binary/wrapper script in /usr/bin
cat << 'EOF' > "$BUILD_DIR/usr/bin/$PACKAGE_NAME"
#!/bin/bash
# Wrapper to run the FastAPI app using the packaged virtual environment.

APP_DIR="/usr/share/mental-wellness-tracker"
VENV_BIN="$APP_DIR/.venv/bin"

if [ ! -d "$VENV_BIN" ]; then
    echo "Virtual environment not found in $APP_DIR. Did the postinst script run successfully?" >&2
    exit 1
fi

cd "$APP_DIR"
exec "$VENV_BIN/python" -m uvicorn main:app "$@"
EOF

chmod +x "$BUILD_DIR/usr/bin/$PACKAGE_NAME"

# 3. Create the Systemd service file
cat << 'EOF' > "$BUILD_DIR/lib/systemd/system/${PACKAGE_NAME}.service"
[Unit]
Description=Mental Wellness Tracker API Service
After=network.target

[Service]
Type=simple
User=wellness-tracker
Group=www-data
WorkingDirectory=/usr/share/mental-wellness-tracker
ExecStart=/usr/bin/mental-wellness-tracker --host 127.0.0.1 --port 8000
Restart=on-failure
Environment=APP_ENV=production
EnvironmentFile=-/etc/default/mental-wellness-tracker

[Install]
WantedBy=multi-user.target
EOF

# 3b. Create Nginx virtual host configuration template
cat << 'EOF' > "$BUILD_DIR/etc/nginx/sites-available/${PACKAGE_NAME}"
server {
    listen 80;
    server_name 0op.in www.0op.in;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# 4. Create the Debian Control File
cat << EOF > "$BUILD_DIR/DEBIAN/control"
Package: $PACKAGE_NAME
Version: $VERSION-$RELEASE
Section: python
Priority: optional
Architecture: $ARCH
Depends: python3, python3-venv, python3-pip
Maintainer: PromptWars Challenger <support@example.com>
Description: AI-powered Mental Wellness Tracker FastAPI app
 A FastAPI + LangChain multi-agent system designed for students.
 Bundle includes API routers, rate limiting, and agent orchestration.
EOF

# 5. Create postinst (Post-Installation Script)
cat << 'EOF' > "$BUILD_DIR/DEBIAN/postinst"
#!/bin/bash
set -e

APP_DIR="/usr/share/mental-wellness-tracker"
USER_NAME="wellness-tracker"

# Create system user for the service if not exists
if ! id -u "$USER_NAME" >/dev/null 2>&1; then
    useradd --system --shell /bin/false --user-group "$USER_NAME"
fi

echo "Setting up Python virtual environment..."
PYTHON_CMD="python3"
if [ -x "/usr/local/bin/python3.14" ]; then
    PYTHON_CMD="/usr/local/bin/python3.14"
elif command -v python3.14 &> /dev/null; then
    PYTHON_CMD="python3.14"
elif command -v python3.13 &> /dev/null; then
    PYTHON_CMD="python3.13"
fi
echo "Using Python: $PYTHON_CMD"

$PYTHON_CMD -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

echo "Setting ownership..."
chown -R "$USER_NAME:www-data" "$APP_DIR"

# Enable and start the systemd service
if [ -d /run/systemd/system ]; then
    systemctl daemon-reload
    systemctl enable mental-wellness-tracker.service
    systemctl restart mental-wellness-tracker.service
fi

echo "Mental Wellness Tracker has been successfully installed and started!"
echo ""
echo "--------------------------------------------------------"
echo "Nginx configuration template installed at:"
echo "  /etc/nginx/sites-available/mental-wellness-tracker"
echo ""
echo "To expose the API on the domain 0op.in:"
echo "1. Symlink the pre-configured Nginx config to sites-enabled:"
echo "   sudo ln -sf /etc/nginx/sites-available/mental-wellness-tracker /etc/nginx/sites-enabled/"
echo "2. Restart Nginx:"
echo "   sudo systemctl restart nginx"
echo "3. Enable HTTPS (SSL) via Certbot:"
echo "   sudo certbot --nginx -d 0op.in -d www.0op.in"
echo "--------------------------------------------------------"
EOF

chmod 755 "$BUILD_DIR/DEBIAN/postinst"

# 6. Create prerm (Pre-Removal Script)
cat << 'EOF' > "$BUILD_DIR/DEBIAN/prerm"
#!/bin/bash
set -e

# Stop and disable systemd service
if [ -d /run/systemd/system ]; then
    systemctl stop mental-wellness-tracker.service || true
    systemctl disable mental-wellness-tracker.service || true
fi
EOF

chmod 755 "$BUILD_DIR/DEBIAN/prerm"

# 7. Build the package
echo "Running dpkg-deb to build the package..."
if command -v dpkg-deb &> /dev/null; then
    dpkg-deb --build "$BUILD_DIR"
    echo "Successfully created ${BUILD_DIR}.deb!"
else
    echo "WARNING: 'dpkg-deb' command not found. Created the directory structure at $BUILD_DIR but could not build the .deb file."
    echo "To build it on a Debian/Ubuntu system, run:"
    echo "  dpkg-deb --build $BUILD_DIR"
fi
