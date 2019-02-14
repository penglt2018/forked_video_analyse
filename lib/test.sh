#!/bin/sh
name=$(basename $0)
dir_name=$(dirname $0)
echo "$name"
echo "$dir_name"
source ./fun.sh

printErr aaa 123
