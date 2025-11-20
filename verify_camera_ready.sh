#!/bin/bash

# verify_camera_ready.sh
# Automated verification script for Thingino/OpenMiko/Dafang camera setup
# Tests connectivity, discovers snapshot URL, checks SSH/temperature access
# Outputs ready-to-use configuration for meters.yaml

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if IP address is provided
if [ -z "$1" ]; then
    echo -e "${RED}Usage: $0 <camera_ip> [ssh_password]${NC}"
    echo ""
    echo "Examples:"
    echo "  $0 10.10.10.207"
    echo "  $0 192.168.1.100 mypassword"
    echo ""
    exit 1
fi

CAMERA_IP="$1"
SSH_PASSWORD="${2:-}"

print_header "Camera Readiness Verification"
echo "Camera IP: $CAMERA_IP"
echo ""

# Test 1: Ping test
print_info "Test 1: Checking network connectivity..."
if ping -c 3 "$CAMERA_IP" > /dev/null 2>&1; then
    print_success "Camera is reachable on network"
else
    print_error "Camera is NOT reachable at $CAMERA_IP"
    print_warning "Check that:"
    echo "  - Camera is powered on"
    echo "  - Camera is connected to WiFi"
    echo "  - IP address is correct"
    echo "  - You're on the same network"
    exit 1
fi

# Test 2: Discover snapshot URL
print_info "Test 2: Discovering snapshot URL..."

# List of common snapshot URLs to try
SNAPSHOT_URLS=(
    "/api/image/snapshot"
    "/api/v1/image/snapshot"
    "/image/snapshot"
    "/snapshot"
    "/snapshot.jpg"
    ":8080/snapshot.jpg"
    "/cgi-bin/currentpic.cgi"
)

SNAPSHOT_URL=""
SNAPSHOT_AUTH=""
FIRMWARE_TYPE=""

for url in "${SNAPSHOT_URLS[@]}"; do
    # Try without authentication first
    if curl -s --max-time 5 "http://${CAMERA_IP}${url}" --output /tmp/test_snapshot_$$.jpg 2>/dev/null; then
        if file /tmp/test_snapshot_$$.jpg | grep -q "JPEG"; then
            SNAPSHOT_URL="http://${CAMERA_IP}${url}"

            # Determine firmware type based on URL
            if [[ "$url" == *"/api/"* ]]; then
                FIRMWARE_TYPE="thingino"
            elif [[ "$url" == *":8080"* ]]; then
                FIRMWARE_TYPE="openmiko"
            elif [[ "$url" == *"cgi-bin"* ]]; then
                FIRMWARE_TYPE="dafang"
            else
                FIRMWARE_TYPE="unknown"
            fi

            print_success "Snapshot URL found: $SNAPSHOT_URL"
            print_info "Detected firmware: $FIRMWARE_TYPE"
            rm -f /tmp/test_snapshot_$$.jpg
            break
        fi
    fi

    # Try with Dafang authentication (root:ismart12)
    if [ -z "$SNAPSHOT_URL" ] && [[ "$url" == *"cgi-bin"* ]]; then
        if curl -s --max-time 5 --user "root:ismart12" "http://${CAMERA_IP}${url}" --output /tmp/test_snapshot_$$.jpg 2>/dev/null; then
            if file /tmp/test_snapshot_$$.jpg | grep -q "JPEG"; then
                SNAPSHOT_URL="http://${CAMERA_IP}${url}"
                SNAPSHOT_AUTH="root:ismart12"
                FIRMWARE_TYPE="dafang"
                print_success "Snapshot URL found (with auth): $SNAPSHOT_URL"
                print_info "Detected firmware: $FIRMWARE_TYPE"
                print_info "Requires authentication: $SNAPSHOT_AUTH"
                rm -f /tmp/test_snapshot_$$.jpg
                break
            fi
        fi
    fi

    rm -f /tmp/test_snapshot_$$.jpg
done

if [ -z "$SNAPSHOT_URL" ]; then
    print_error "Could not discover snapshot URL"
    print_warning "Tried the following URLs:"
    for url in "${SNAPSHOT_URLS[@]}"; do
        echo "  - http://${CAMERA_IP}${url}"
    done
    print_info "You may need to check camera web interface for snapshot settings"
    exit 1
fi

# Test 3: SSH connectivity
print_info "Test 3: Checking SSH access..."

SSH_AVAILABLE=false
SSH_USER="root"

# Try SSH without password first (key-based)
if ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$SSH_USER@$CAMERA_IP" "echo 'SSH OK'" > /dev/null 2>&1; then
    SSH_AVAILABLE=true
    print_success "SSH access available (key-based authentication)"
elif [ -n "$SSH_PASSWORD" ]; then
    # Try with provided password using sshpass if available
    if command -v sshpass > /dev/null 2>&1; then
        if sshpass -p "$SSH_PASSWORD" ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$SSH_USER@$CAMERA_IP" "echo 'SSH OK'" > /dev/null 2>&1; then
            SSH_AVAILABLE=true
            print_success "SSH access available (password authentication)"
        else
            print_warning "SSH password authentication failed"
        fi
    else
        print_warning "sshpass not installed, cannot test password-based SSH"
        print_info "Install sshpass to test SSH with password: brew install sshpass (macOS) or apt install sshpass (Linux)"
    fi
else
    print_warning "SSH access not available (no password provided)"
    print_info "Provide SSH password as second argument to test SSH: $0 $CAMERA_IP <password>"
fi

# Test 4: Temperature reading (if SSH available)
print_info "Test 4: Checking temperature sensor access..."

TEMPERATURE_AVAILABLE=false
TEMPERATURE_VALUE=""

if [ "$SSH_AVAILABLE" = true ]; then
    if [ -n "$SSH_PASSWORD" ] && command -v sshpass > /dev/null 2>&1; then
        TEMP_RAW=$(sshpass -p "$SSH_PASSWORD" ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$SSH_USER@$CAMERA_IP" "cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null" || echo "")
    else
        TEMP_RAW=$(ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$SSH_USER@$CAMERA_IP" "cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null" || echo "")
    fi

    if [ -n "$TEMP_RAW" ] && [ "$TEMP_RAW" -gt 0 ] 2>/dev/null; then
        TEMPERATURE_AVAILABLE=true
        TEMP_CELSIUS=$(echo "scale=1; $TEMP_RAW / 1000" | bc)
        TEMP_FAHRENHEIT=$(echo "scale=1; ($TEMP_CELSIUS * 9 / 5) + 32" | bc)
        TEMPERATURE_VALUE="${TEMP_CELSIUS}°C (${TEMP_FAHRENHEIT}°F)"
        print_success "Temperature reading available: $TEMPERATURE_VALUE"
    else
        print_warning "Temperature sensor not accessible via SSH"
    fi
else
    print_warning "Temperature reading requires SSH access"
fi

# Test 5: Download test snapshot
print_info "Test 5: Downloading test snapshot..."

TEST_SNAPSHOT="/tmp/camera_test_${CAMERA_IP}_$$.jpg"

if [ -n "$SNAPSHOT_AUTH" ]; then
    curl -s --user "$SNAPSHOT_AUTH" "$SNAPSHOT_URL" --output "$TEST_SNAPSHOT"
else
    curl -s "$SNAPSHOT_URL" --output "$TEST_SNAPSHOT"
fi

if file "$TEST_SNAPSHOT" | grep -q "JPEG"; then
    FILE_SIZE=$(ls -lh "$TEST_SNAPSHOT" | awk '{print $5}')
    IMAGE_DIMENSIONS=$(sips -g pixelWidth -g pixelHeight "$TEST_SNAPSHOT" 2>/dev/null | tail -2 | awk '{print $2}' | tr '\n' 'x' | sed 's/x$//')

    print_success "Test snapshot downloaded successfully"
    print_info "File size: $FILE_SIZE"
    print_info "Dimensions: $IMAGE_DIMENSIONS"
    print_info "Saved to: $TEST_SNAPSHOT"

    # Optionally open image for visual inspection
    if command -v open > /dev/null 2>&1; then
        print_info "Opening image for visual inspection..."
        open "$TEST_SNAPSHOT"
    fi
else
    print_error "Downloaded file is not a valid JPEG image"
    exit 1
fi

# Summary and configuration output
print_header "Verification Summary"

echo "Camera Status: ${GREEN}READY${NC}"
echo ""
echo "Camera Details:"
echo "  IP Address:        $CAMERA_IP"
echo "  Firmware Type:     $FIRMWARE_TYPE"
echo "  Snapshot URL:      $SNAPSHOT_URL"
if [ -n "$SNAPSHOT_AUTH" ]; then
    echo "  Authentication:    $SNAPSHOT_AUTH"
fi
echo "  SSH Access:        $([ "$SSH_AVAILABLE" = true ] && echo "${GREEN}Available${NC}" || echo "${YELLOW}Not Available${NC}")"
echo "  Temperature:       $([ "$TEMPERATURE_AVAILABLE" = true ] && echo "${GREEN}Available${NC} ($TEMPERATURE_VALUE)" || echo "${YELLOW}Not Available${NC}")"
echo ""

# Generate meters.yaml configuration
print_header "Ready-to-Use Configuration"

echo "Add this to your config/meters.yaml:"
echo ""
echo "---"
echo ""

cat << EOF
meters:
  water_main:  # Change this to your meter name
    name: "Water Main"
    camera:
      type: "$FIRMWARE_TYPE"
      ip: "$CAMERA_IP"
      snapshot_url: "$SNAPSHOT_URL"
EOF

if [ "$SSH_AVAILABLE" = true ] && [ -n "$SSH_PASSWORD" ]; then
cat << EOF

      # SSH credentials for temperature reading (optional)
      ssh_user: "$SSH_USER"
      ssh_password: "$SSH_PASSWORD"
EOF
fi

cat << EOF

    meter:
      type: "badger_absolute_digital"  # Change to your meter type
      digits: 5
      has_dial: true
EOF

echo ""
echo "---"
echo ""

# Next steps
print_header "Next Steps"

echo "1. Copy the configuration above to config/meters.yaml"
echo ""
echo "2. Test meter reading:"
echo "   ${BLUE}/takemetersnapshot${NC}"
echo "   or"
echo "   ${BLUE}python3 run_meter_reading.py${NC}"
echo ""
echo "3. View snapshot history:"
echo "   ${BLUE}./start_snapshot_viewer.sh${NC}"
echo "   Open: http://127.0.0.1:5001"
echo ""

if [ "$SSH_AVAILABLE" = false ]; then
    print_warning "To enable temperature reading:"
    echo "  1. Enable SSH in camera web interface"
    echo "  2. Set SSH password"
    echo "  3. Re-run this script with password: $0 $CAMERA_IP <ssh_password>"
    echo ""
fi

print_success "Camera verification complete!"
print_info "Test snapshot saved to: $TEST_SNAPSHOT"
echo ""
