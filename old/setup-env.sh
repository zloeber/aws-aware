# Helper script to condense configuration to just 2 
# parameters, the environment and the application
# Both parameters should be case-sensitive for your
# ./profile/<application>-<env>.env file.
#
# USAGE: ./setup.env.sh team1 uat

mkdir -p ./profiles
# Choose an application to deploy (team1/team2)
export MY_APP=$1

# Choose an environment to deploy (uat or prod)
export MY_ENV=$2

# Our base environment definition
export MY_DEPLOY_TEMPLATE="./profiles/${MY_APP}-${MY_ENV}.env"

# Setup a new app configuration based on deployment file,
# then run the default set of threshold monitors with new config
# (Note: ensure things work and look as you would expect in the email)
make dpl=${MY_DEPLOY_TEMPLATE} run-app-config run-app

# Create a scheduled task (4 hours by default) with new config
# (Note: This updates ${HOME}/.local/bin/auto-aws-aware.sh as well)
# make dpl=${MY_DEPLOY_TEMPLATE} install-cron-task

# If you want to ensure your makefile targets your env file by default
#mv ./deploy.env ./deploy.old
#ln -s ./profiles/team1-prod.env ./deploy.env
