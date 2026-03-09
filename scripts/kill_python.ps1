# This script stops all running Python processes.
Get-Process -Name "python" -ErrorAction SilentlyContinue | Stop-Process -Force
