#!/bin/bash

# Set number of UEs (default 5, can be modified via parameter)
NUM_UES=${1:-5}
TARGET_IP="8.8.8.8"
PING_COUNT=4  # Number of pings per UE

echo "Starting multi-UE ping test..."
echo "Number of UEs: $NUM_UES"
echo "Target IP: $TARGET_IP"
echo "Ping count per UE: $PING_COUNT"
echo "================================"

# Store PIDs of all background processes
pids=()

# Start ping process for each UE
for i in $(seq 0 $((NUM_UES-1))); do
    interface="uesimtun$i"
    echo "Starting UE $((i+1)) - using interface: $interface"
    
    # Check if network interface exists
    if ip link show "$interface" &> /dev/null; then
        echo "  ✓ Interface $interface exists, starting ping..."
        # Run ping in background and redirect output to separate files
        ping -I "$interface" -c "$PING_COUNT" "$TARGET_IP" > "ping_ue$((i+1))_${interface}.log" 2>&1 &
        pids+=($!)
        echo "  → UE $((i+1)) ping process started (PID: ${pids[-1]})"
    else
        echo "  ✗ Warning: Interface $interface does not exist, skipping this UE"
    fi
    
    sleep 0.5  # Small delay to avoid starting too many processes simultaneously
done

echo "================================"
echo "All UE ping processes started, waiting for completion..."

# Wait for all background processes to complete
for pid in "${pids[@]}"; do
    wait "$pid"
done

echo "================================"
echo "All ping tests completed! View results:"

# Display ping result summary for each UE
for i in $(seq 0 $((NUM_UES-1))); do
    logfile="ping_ue$((i+1))_uesimtun$i.log"
    if [ -f "$logfile" ]; then
        echo ""
        echo "UE $((i+1)) (uesimtun$i) result summary:"
        echo "------------------------"
        # Display ping statistics
        tail -3 "$logfile" | head -2
        echo "Full log: $logfile"
    fi
done

echo ""
echo "Test completed! All log files saved in current directory."