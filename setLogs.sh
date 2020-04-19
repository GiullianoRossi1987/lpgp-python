#!/bin/bash

echo " ==== CONFIGURING LOGS FILES ==== "

echo "Configuring general.log"
touch logs/general.log || {
  chmod 744 -R logs
  touch logs/general.log
  echo "general.log done!"
}
echo "Configuring client-mysql.log ..."
touch logs/client-mysql.log || {
  chmod 744 -R logs
  touch logs/client-mysql.log
  echo "client-mysql.log done!"
}
echo "Configuring error.log ... "
touch logs/error.log || {
  chmod 744 -R logs
  touch logs/error.log
  echo "error.log done!"
}

echo " ==== ALL FILES CONFIGURED ==== "