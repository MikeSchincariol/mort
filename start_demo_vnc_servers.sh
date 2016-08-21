#!/bin/bash

vncserver -kill :1
vncserver -kill :2
vncserver -kill :3
vncserver -kill :4

vncserver :1 -geometry 1280x900 -depth 16
vncserver :2 -geometry 1280x900 -depth 16
vncserver :3 -geometry 1280x900 -depth 16
vncserver :4 -geometry 1280x900 -depth 16


