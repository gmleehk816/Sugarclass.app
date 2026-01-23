# Sugarclass.app - Remote Deploy Trigger
# Run this from your local computer to update the VPS

$VPS_IP = "156.238.242.71"
$REMOTE_PATH = "/var/www/Sugarclass.app/update.sh"

Write-Host "📡 Connecting to $VPS_IP and triggering update..." -ForegroundColor Cyan

ssh root@$VPS_IP "bash $REMOTE_PATH"

Write-Host "🎉 Deployment trigger finished!" -ForegroundColor Green
