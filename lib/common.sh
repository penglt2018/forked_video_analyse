#!/bin/bash

########################################################################################
#
# Program Name: Common Functions
# File Name: common.sh
# Creation Date: Apr 2018
# Programmer: XINWU LIU
# Abstract: This script is for providing common functions
# Entry Condition: N/A
# Exit Condition: N/A
# Example: N/A
# Program Message: N/A
# Remarks: N/A
# Amendment Hisotry:
#			Version:
#			Date:
#			Programmer:
#			Reason:
#
########################################################################################

sh_name=$(basename $0)

################################
# Print Error and Exit
################################
function printErr() {
	local msg="$1"
	[ -z "$msg" ] && echo "printErr() Error: message $msg is NOT given!" && exit 998
	local rt_cod="$2"
	[ -z $rt_cod ] && echo "printErr() Error: return code is NOT given!" && exit 997
	isInt "$rt_cod"
	echo "$msg" && exit $rt_cod
}

################################
# Integer Check
################################
function isInt() {
	local num="$1"
	#[ -z "$1" ] && echo "isNum() Error: input $num is None!" && exit 999
	num=`echo "$rt_cod" |sed 's/[0-9]//g'`
	[ ! -z "$num" ] && echo "isNum() Error: input $num is NOT an integer!" && exit 800
}

################################
# File Existence Check
################################
function ckFileExist() {
	local file="$1"
	#echo "$file"
	[ ! -f "$file" ] && printErr "Error: file $file does NOT exist!" 11
	[ ! -r "$file" ] && printErr "Error: file $file is NOT readable!" 12
}

################################
# Dir Existence Check
################################
function ckDirExist() {
	local dir="$1"
	[ ! -d "$dir" ] && printErr "Error: path $dir dose NOT exist!" 21
}


################################
# return check
################################
function rtCheck() {
	local rt_cod="$1"
	local cmd="$2"
	[ "$1" -ne 0 ] && printErr "Error: execution failed. $cmd" 22
}
