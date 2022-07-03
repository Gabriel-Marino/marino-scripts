#!/bin/bash
set -euo pipefail

for dir in */; do
	echo $dir | sed -e 's/^/  repo: /g;s/\///g;s/[a-z]/\U&/g'
	cd $dir
	git status -sb
	git branch --format='%(HEAD) %(color:yellow)%(refname:short)%(color:reset) - %(contents:subject) %(color:green)(%(committerdate:relative)) [%(authorname)]' --sort=-committerdate
	cd ..
done
