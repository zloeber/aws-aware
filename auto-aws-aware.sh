THISENV=local

APP_PATH=${HOME}/.local/bin/aws-aware
BASE_MONITOR="${HOME}/aws-aware/config/default-monitor.yml"

APP_ING_CFG="${HOME}/aws-aware/config/team1-${THISENV}-config.yml"
APP_COMP_CFG="${HOME}/aws-aware/config/team-comp-${THISENV}-config.yml"

ING_MONITORS="${HOME}/aws-aware/config/team1-${THISENV}-monitor.yml"
COMP_MONITORS="${HOME}/aws-aware/config/team-comp-${THISENV}-monitor.yml"

echo "Downloading base instance data first..."
$APP_PATH -configfile "${APP_ING_CFG}" run -includeundefined -force -monitorconfig "${BASE_MONITOR}" export_data

APPS=( team1 team2 )

for app in "${APPS[@]}"
do
	echo "Processing: ${app}-${THISENV}"
    APP_CFG="${HOME}/aws-aware/config/${app}-${THISENV}-config.yml"
    MON_CFG="${HOME}/aws-aware/config/${app}-${THISENV}-monitor.yml"
    $APP_PATH -configfile ${APP_CFG} run -monitorconfig "${MON_CFG}" -sendalerts -includeundefined -force -skipprobe monitors
done
