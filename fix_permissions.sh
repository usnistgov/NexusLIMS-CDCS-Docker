#!/bin/bash

# run this script from this directory before building things if you run into 
# odd permission errors
# (this is due to umask being set more restrictive than usual)

for f in $(find . -mindepth 1 | grep -v ".git"); do
    mod=$(stat -c "%a" $f)
    cmod="$(echo $mod | cut -c1)$(echo $mod | cut -c2)$(echo $mod | cut -c2)"
    echo "$f: $mod -> $cmod"
    chmod $cmod $f
done
