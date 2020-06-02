# prod/uat
ENV=${ENV:-${1:-prod}}
# team1/team-comp
TEAM=${TEAM:-${2:-team1}}

# Local bin path (cron jobs)
APP_PATH=${APP_PATH:-"${HOME}/.local/bin/aws-aware"}
APP_CFG=${APP_CFG:-"../config/${TEAM}-${ENV}-config.yml"}
MON_CFG=${MON_CFG:-"../config/${TEAM}-${ENV}-monitor.yml"}

echo "App Path: ${APP_PATH}"
echo "App Config: ${APP_CFG}"
echo "Mon Config: ${MON_CFG}"
echo "Environment: ${ENV}"
echo "Team: ${TEAM}"
echo " "

echo "Beginning initial data export."
echo "${APP_PATH}" -configfile "${APP_CFG}" run -includeundefined -force report -reportname "${ENV}_instances.html"

echo "Generating filtered report."
echo "${APP_PATH}" -configfile "${APP_CFG}" run -includeundefined -skipprobe -force report -reportname "${ENV}_thresholds_${TEAM}.html" -filteredinstances

echo "Running threshold monitor."
echo "${APP_PATH}" -configfile "${APP_CFG}" run -sendalerts -includeundefined -skipprobe monitors -monitorconfig "${MON_CFG}"


