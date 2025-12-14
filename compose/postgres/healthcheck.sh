#!/usr/bin/env bash

pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"
