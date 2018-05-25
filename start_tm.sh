#!/usr/bin/env bash

rm -rf .potato
tendermint init --home .potato
cp config.toml .potato/config/config.toml
tendermint --home .potato node
