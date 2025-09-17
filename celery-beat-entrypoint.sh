#!/bin/bash

celery -A config beat -l info --schedule=./celerybeat-schedule
