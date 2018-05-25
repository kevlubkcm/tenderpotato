#!/usr/bin/env bash

rm -rf .potato
tendermint init --home .potato
tendermint --home .potato node
