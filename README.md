# CucoLogger

CucoLogger (Current Cost Logger) is a program to log the data from a [Current
Cost Envi CC128][1] and try and make useful things with it.

[1]: http://currentcost.com/product-envi.html

## Installation

Cucologger cannot be installed yet. It has to be run from its own directory.

### Dependencies

 - recent enough python (tested with 2.7.3, probably works with older versions)
   http://www.python.org/
 - Linux kernel, the code that detects on what port the CC128 can be found is
   Linux specific (tested with 3.2.0)
 - python-rrdtool (tested with 1.4.7) http://oss.oetiker.ch/rrdtool/
 - BeautifulSoup (tested with 3.2.0)
   http://www.crummy.com/software/BeautifulSoup
 - python-serial (tested with 2.5.2 ) http://pyserial.sourceforge.net

### Configuration

CucoLogger requires a configuration file. The `cucologger.py` executable looks
for a configuration file in the current directory called `cucologger.conf`.
The path of an alternative configuration file can be passed as parametter to
`cucologger.py`.

## Running

Make sure that your CC128 is plugged to your computer, that you have a
configuration file ready and run:

    cucologger.py /path/to/cucologger.conf

You don't need to pass the configuration file path if it is called
`cucologger.conf` and sits in the current directory.
