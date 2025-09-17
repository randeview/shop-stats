#!/bin/bash

celery -A config worker -Q mcf_credits --loglevel=info
