#!/bin/bash

sed -e '/ALLFUNCTIONS/ { 
r bootstrap-functions
d 
}' init.sh
