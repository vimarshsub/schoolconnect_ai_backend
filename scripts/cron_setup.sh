#!/bin/bash

# Cron job setup script for SchoolConnect-AI Backend

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or with sudo"
  exit 1
fi

# Get the absolute path to the project directory
PROJECT_DIR=$(cd "$(dirname "$0")/.." && pwd)
echo "Project directory: $PROJECT_DIR"

# Create the cron job script
CRON_SCRIPT="$PROJECT_DIR/scripts/run_sync.sh"
cat > "$CRON_SCRIPT" << EOL
#!/bin/bash
cd $PROJECT_DIR
source venv/bin/activate
python -c "from src.data_ingestion.tasks.fetch_announcements import FetchAnnouncementsTask; task = FetchAnnouncementsTask(); task.execute('USERNAME', 'PASSWORD')" >> $PROJECT_DIR/sync.log 2>&1
EOL

# Make the script executable
chmod +x "$CRON_SCRIPT"

# Add the cron job to run daily at midnight
CRON_JOB="0 0 * * * $CRON_SCRIPT"
(crontab -l 2>/dev/null | grep -v "$CRON_SCRIPT" ; echo "$CRON_JOB") | crontab -

echo "Cron job installed to run daily at midnight."
echo "IMPORTANT: Edit $CRON_SCRIPT to set your SchoolConnect username and password."
echo "You can change the schedule by editing the crontab (run: crontab -e)"
