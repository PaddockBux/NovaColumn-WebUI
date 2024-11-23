# NovaColumn WebUI

WebUI + API for the NovaColumn database.

## Prerequisites

NCWebUI requires a database formatted by [NovaColumnV2](https://github.com/PaddockBux/NovaColumnV2), Python3.8+, and any webserver such as [apache](https://httpd.apache.org/) or [nginx](https://www.nginx.com/) to host the website.

## Installation

First, clone the repo with `git clone https://github.com/PaddockBux/NovaColumn-WebUI` and then cd into the directory.

Then install the requirements by running `pip install -r requirements.txt` or `python -m pip install -r requirements.txt`.

## Usage

In order to use the webui, you'll first need to edit the `index.html` field accordingly.\
If you are using this for personal or development purposes, you will not need to do this as it is already set to localhost and default port.

To setup NCWebUI for production or shared use, you will need to edit line 165 in `index.html` and set the fetch URL to the API's public endpoint.

To run the API, simply run the script with the correct database credentials: `python api.py localhost root password novacolumn`

The help page (`python api.py -h`) has all of the details of use:

```text
usage: api.py [-h] [--dbport DBPORT] [--port PORT] host username password database

           _  __              _____     __                   _      __    __   __  ______
          / |/ /__ _  _____ _/ ___/__  / /_ ____ _  ___  ___| | /| / /__ / /  / / / /  _/
         /    / _ \ |/ / _ `/ /__/ _ \/ / // /  ' \/ _ \/___/ |/ |/ / -_) _ \/ /_/ // /
        /_/|_/\___/___/\_,_/\___/\___/_/\_,_/_/_/_/_//_/    |__/|__/\__/_.__/\____/___/
                                     NovaColumn-WebUI
           Programmed by & main ideas guy: GoGreek    ::    Co-ideas guy: Draxillian

positional arguments:
  host             host IP of the database
  username         database username to use.
  password         database password to use.
  database         database password to use.

options:
  -h, --help       show this help message and exit
  --dbport DBPORT  use a different database port. (default 3306)
  --port PORT      use a different API port instead of default (8080).

Use case:
python api.py localhost root password novacolumn

Output translation:
[GET] (random unique server) / (latest uid from server) - ((IP foreign key), (port))
```

## Contributing

Pull requests must be clear and concise.\
If you want to add a new feature, please open an issue first to discuss. Issues with no clarification or reason (add x because yes) will be closed.

## License

This project is licensed under the AGPL-3.0 License - see the [LICENSE](./LICENSE) file for details.
