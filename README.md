### DISPLAY

** DISCLAIMER **

This repo is a 1-to-1 port of the codebase that is used in the CCDCOE LOCKED SHIELDS (LS) exercise 
and is published on specific request for general use. Although the general setup and layout of the 
application is ment to be 'generic'; during the development of the last 4 years some corners 
almost certainly where cut to match specific LS requirements or LS limitations. 

Inadvertently 'new' users will bump into these 'specifics' when setting up or operating the display 
instance. In addition to this most of the development was done in the context of experimentation and
(temporarily) exercise support; due to these facts the application lacks a lot of development best 
practices in terms of documentation, architecture drawings or proper development instructions. 
The maintainers are, obviously, aware of this; please don't hesitate to file issues (or even better PR's ;-) ) 
for 'things' you mis / find. We'll try to accomodate / support to our full extend wherever possible. 

<!-- start into-documentation -->
## Purpose

The display application creates, based on a certain interval, screenshots of predefined websites. The application 
facilitates a web interface which (based on the configuration) has multiple tabs which will hold either a single target 
for all blue teams, or all targets for a single blue team. The web interface gives an overview of the latest 
screenshots and provides ways to download, create or display the latest screenshots. Besides the screenshots the 
application will provide evidence shots (iaw the LS ROE's and suitable for EXPO) of sites that are found to have 
changed state since the last taken screenshot. All screenshots for a site are stored in a timeline which will provide 
an insight (or backlog) of state changes over time.

Besides the web interface display also composes a (currently very limited) web API for creating and downloading 
screen / evidence shots.
<!-- end into-documentation -->

## Documentation

Please refer to our documentation [here](#)
