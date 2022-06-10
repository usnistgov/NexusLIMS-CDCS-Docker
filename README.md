# NexusLIMS Docker Deployment

NexusLIMS is a laboratory information management system developed for the use of the Electron Microscopy Nexus co-op
at the National Institute of Standards and Technology (NIST) and made publicly available to encourage other institutions
to consider practices to make their data more [FAIR](https://www.go-fair.org/fair-principles/) and open. 
NexusLIMS is described by a manuscript published in 
[_Microscopy and Microanalysis_](https://doi.org/10.1017/S1431927621000222), and consists of a "back-end" system
to automatically generate research experimental records from electron microscopy sessions (available 
[here](https://github.com/usnistgov/NexusLIMS/)) and a "front-end" web application that acts as the primary user
interface for viewing, querying, and downloading research data and experimental records. 

This repository contains files and documentation about how to build and deploy the 
[CDCS](https://www.nist.gov/itl/ssd/information-systems-group/configurable-data-curation-system-cdcs/about-cdcs)-based
front-end for NexusLIMS. The code in this repository is a fork of the deployment code provided by the
[CDCS development team](https://github.com/usnistgov/cdcs-docker/), customized and further documented for use with the
[NexusLIMS CDCS](https://github.com/usnistgov/nexuslims-cdcs) code.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Overall Approach](#overall-approach)
- [1. Build Docker Image](#step-1-build-the-nexuslims-cdcs-docker-image)
  - [Customize Build Environment](#11-customize-the-build-environment-values)
  - [Build Image](#12-build-the-image)
- [2. Configure the NexusLIMS Docker Container](#step-2-deploy-the-nexuslims-cdcs-application)
  - [Customize Deploy Environment](#21-customize-the-deploy-environment-values)
  - [Configure SAML Single Sign On (optional)](#22-optional-saml-security-assertion-markup-language-single-sign-on-sso)
    - [Set up SAML Contacts](#221-saml-contact-person-and-organization-environment-variables)
  - [Configure Handle Server Integration (optional)](#23-optional-handle-server-configuration-for-persistent-identifiers-pids)
  - [Configure Other Application Settings (optional)](#24-optional-configure-other-application-settings---advanced)
- [3. Run the NexusLIMS Application](#step-3-run-the-nexuslims-cdcs-application)
- [4. Create CDCS Superuser](#step-4-create-a-superuser)
- [5. Access NexusLIMS Web Application](#step-5-try-to-access-the-nexuslims-application)
- [6. Stopping the Application](#step-6-stopping-the-nexuslims-application)
- [Appendices](#appendix-a-troubleshooting)
  - [Troubleshooting](#appendix-a-troubleshooting)
  - [Configuring Additional Components](#appendix-b-additional-components)
  - [Other Potentially Useful Scripts](#appendix-c-other-helper-scripts-included-in-this-repository)
  - [Working with the CDCS Databases](#appendix-d-working-with-the-information-in-the-cdcs-databases-directly)

## Prerequisites

These instructions assume you have both [Docker](https://docs.docker.com/engine/install/) and 
[Docker Compose](https://docs.docker.com/compose/install/) installed on your system. If you are using "Docker Desktop",
then Docker Compose comes preinstalled. Otherwise, you will need to install Docker Compose manually following the
instructions in the previous link.

The instructions below also assume you have downloaded the files in this repository via `git clone` or manually from
the Github/Gitlab interface and extracted them to a folder on your local machine or server on which you plan to deploy.

## Overall approach

There are two primary steps to getting a working CDCS deployment. The first is to build the Docker image for the
CDCS web application. The files to do so are provided in the `./build` folder. Once that image is built, you will need
to use the files in the `./deploy` folder to actually run the application, together with the supporting tools
(PostgreSQL, Nginx, MongoDB, and Redis). These supporting tools are automatically downloaded and deployed via 
Docker Compose (see the `./deploy/docker-compose.yml` file for details), so you will not need to install/download
anything other than the files in this repository to run the NexusLIMS front-end. 

## Step 1: Build the NexusLIMS CDCS docker image

As mentioned, the first step is to build the Docker image that will be used in the latter stages when running the actual
application

### 1.1: Customize the build environment values

As with many Docker deployments, the configuration settings are controlled by environment variables, which should
be customized to your needs. These are controlled by editing the values in the `.env` file in the `./build` folder.
Defaults are provided in the file included with the repository, but you can adjust them if required. Make sure to edit
this file with a simple text/code editor (`notepad.exe` works on Windows) or using a command line editor (i.e. `nano`,
`vi`, `emacs`, etc.).

Below is the list of environment variables that need to be included in the `.env` file and their description:

| Variable       | Description                                                                                                                                                                   |
|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| PROJECT_NAME   | Used internally to name the containers and executables; should not be changed from "`mdcs`"                                                                                   |
| IMAGE_NAME     | Name of the resulting image after building; default is `nexuslims`; can be changed, but will need to be updated later in the `./deploy` settings as well                      |
| IMAGE_VERSION  | Version of the image to build; recommended to leave this as the default; version number tracks the upstream MDCS version                                                      |
| CDCS_REPO      | URL of the NexusLIMS-CDCS repository to clone from when building the image (e.g. https://github.com/usnistgov/nexuslims-cdcs.git)                                             |
| BRANCH         | Branch/Tag of the repository specified in `CDCS_REPO` that will be used to build the image; recommended to leave as `NexusLIMS_master` unless you require something different |
| PIP_CONF       | Pip configuration file to use to build the image (this is a mostly deprecated setting, so just leave as the default `pypi`)                                                   |
| PYTHON_VERSION | Version of the Python image to use as a base image for the CDCS image (should leave as default as that is the only tested version)                                            |


### 1.2: Build the image

To build the image, change directories into the `./build` folder and simply run the following `docker-compose` command.
This will instruct Docker Compose to read `./build/docker-compose.yml`, which in turn specifies that Docker should
build an image as specified in the `./build/cdcs/Dockerfile` file. This will take care of fetching the code 
(via git) from the repository specified in the `CDCS_REPO` variable, and then building

``` bash
$ docker-compose build
```

## Step 2: Deploy the NexusLIMS CDCS application

Assuming the build process did not present any errors, you are now ready to proceed to the deployment steps described
below. You can confirm the image was built and is now on your system by running `docker image list`, which should show
the `nexuslims` (or whatever name you specified in the `IMAGE_NAME` setting) image in the output.

There are many configurations possible when deploying a CDCS-based application, depending on your needs for 
SSL encryption, integration with a handle server, single-sign-on, enabling of ElasticSearch, etc. The instructions
provided below will present the simplest case: no SSL (i.e. `http://` rather than `https://`) and no other features
enabled. Descriptions of how to enable these other features are included in sections marked "(optional)" in case you
wish to try to use them, but they are not required for the basic installation.

### 2.1: Customize the deploy environment values

Just as was done with the image build process, you will need to edit the `./deploy/.env` file to configure the settings
for the application. This file has many more options than the `./build/.env` file, since they configure many parts
of how the application actually runs. The environment variables that can be set and their description are listed below.
There is also documentation in the `./deploy/.env` file itself for each value which can provide additional context.
In general, if you are not sure about a value, it is probably safest to leave it its default if you are just trying to 
do a simple local installation.

| Variable              | Description                                                                                                                                                                                                     |
|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| PROJECT_NAME          | Used internally to name the containers and executables; should not be changed from "`mdcs`"                                                                                                                     |
| IMAGE_NAME            | Name of the NexusLIMS Docker image to deploy; should be `nexuslims` unless it was changed in the `./build/.env` file                                                                                            |
| IMAGE_VERSION         | Version of the NexusLIMS Docker image to deploy; should be whatever was set in the `./build/.env` file                                                                                                          |
| HOSTNAME              | Hostname of the server; for local deployment, use the machine's IP address, such as 192.168.1.10; otherwise use the server's [FQDN](https://en.wikipedia.org/wiki/Fully_qualified_domain_name)                  |
| SERVER_URI            | URI of server; for local deployment use the machine's IP address prefixed with `http` or `https`, depending on whether or not you are using SSL; e.g. `http://192.168.1.10`                                     |
| ALLOWED_HOSTS         | Comma-separated list of hosts that will be allowed to access the application (e.g. `ALLOWED_HOSTS=127.0.0.1,localhost`), see [Allowed Hosts](https://docs.djangoproject.com/en/2.2/ref/settings/#allowed-hosts) |
| SERVER_NAME           | Name of the server (e.g. NexusLIMS) used to configure some text in the application                                                                                                                              |
| SETTINGS              | The settings file to use during deployment (see the [Settings](#settings) for more details). Probably best to leave as the default value if you want a simple local installation                                |
| SERVER_CONF           | Controls the nginx configuration (e.g. `default` for http, or `https` for SSL. The protocol of the `SERVER_URI` variable should be updated accordingly                                                          |
| MONGO_PORT            | Port to use for MongoDB (default: 27017)                                                                                                                                                                        |
| MONGO_ADMIN_USER      | Admin user to use for MongoDB (default: `mongo_admin`; should be different from `MONGO_USER`)                                                                                                                   |
| MONGO_ADMIN_PASS      | Admin password to use for MongoDB (this needs to be changed before deployment)                                                                                                                                  |
| MONGO_USER            | Regular user for MongoDB (default: `curator`; should be different from `MONGO_ADMIN_USER`)                                                                                                                      |
| MONGO_PASS            | User password for MongoDB (this needs to be changed before deployment)                                                                                                                                          |
| MONGO_DB              | Name of the Mongo database to use (default: `cdcs`)                                                                                                                                                             |
| POSTGRES_PORT         | Port to use for PostgreSQL server (default: 5432)                                                                                                                                                               |
| POSTGRES_USER         | Regular user for Postgres (default: `curator`)                                                                                                                                                                  |
| POSTGRES_PASS         | Regular user password for Postgres (this needs to be changed before deployment)                                                                                                                                 |
| POSTGRES_DB           | Name of the Postgres database (default: `cdcs`)                                                                                                                                                                 |
| REDIS_PORT            | Redis Port (default: 6379)                                                                                                                                                                                      |
| REDIS_PASS            | Password for Redis (this needs to be changed before deployment)                                                                                                                                                 |
| DJANGO_SECRET_KEY     | [Secret Key](https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/#secret-key) for Django (should be a "large random value" and changed prior to deployment)                                        |
| NGINX_PORT_80         | HTTP port to expose on host machine for NGINX (default: 80; only needs to be changed if you already have a service running on port 80)                                                                          | 
| NGINX_PORT_443        | HTTPS port to expose on host machine for NGINX (default: 443; only needs to be changed if you already have a service running on port 443)                                                                       |
| MONGO_VERSION         | Version of the MongoDB Docker image to user (best left as default, as that is the only version actively tested)                                                                                                 |
| REDIS_VERSION         | Version of the Redis image  (best left as default, as that is the only version actively tested)                                                                                                                 |
| POSTGRES_VERSION      | Version of the Postgres image  (best left as default, as that is the only version actively tested)                                                                                                              |
| NGINX_VERSION         | Version of the NGINX image  (best left as default, as that is the only version actively tested)                                                                                                                 |
| UWSGI_PROCESSES       | Number of [`uwsgi`](https://uwsgi-docs.readthedocs.io/en/latest/) processes to start (default: 10)                                                                                                              |
| MONITORING_SERVER_URI | URI of an APM server for monitoring (recommended to omit or leave blank unless you have need for monitoring)                                                                                                    |

A few additional environment variables are provided to the NexusLIMS Docker container. The variables below are computed
based on the values of other variables. If changed, some portions of the `docker-compose.yml` might need to be updated
to stay consistent:

| Variable               | Description                                                                                                                                                              |
|------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| DJANGO_SETTINGS_MODULE | [`DJANGO_SETTINGS_MODULE`](https://docs.djangoproject.com/en/2.2/topics/settings/#envvar-DJANGO_SETTINGS_MODULE) (set using the values of `PROJECT_NAME` and `SETTINGS`) |
| MONGO_HOST             | Mongodb hostname (set to `${PROJECT_NAME}_cdcs_mongo`)                                                                                                                   |
| POSTGRES_HOST          | Postgres hostname (set to `${PROJECT_NAME}_cdcs_postgres`)                                                                                                               |
| REDIS_HOST             | REDIS hostname (set to `${PROJECT_NAME}_cdcs_redis`)                                                                                                                     |


### 2.2: (optional) SAML (Security Assertion Markup Language) Single-Sign On (SSO)

The CDCS platform (on which NexusLIMS is built) supports SSO authentication via SAML (commonly used in enterprise
environments). If you wish to use this feature, you will have to configure SAML authentication by providing values for
the following environment variables in the `saml2/.env` file (which will be read by the `docker-compose.yml` file and
used when the application is started). See `saml2/.env.example` for an example of SAML2 configuration.

If you do not wish to use SAML authentication and instead want to use the built-in user management, simply do nothing
and skip this entire section, as the default is to *disable* SAML via the `ENABLE_SAML2_SSO_AUTH=False` setting.

| Variable                        | Description                                                                                                                                                                                  |
|---------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ENABLE_SAML2_SSO_AUTH           | Enable SAML2 authentication (e.g. `ENABLE_SAML2_SSO_AUTH=True`)                                                                                                                              |
| SAML_ATTRIBUTE_MAP_DIR          | Points to a directory which has the attribute maps in Python modules (see [attribute_map_dir](https://pysaml2.readthedocs.io/en/latest/howto/config.html#attribute-map-dir))                 |
| SAML_ATTRIBUTES_MAP_IDENTIFIER  | SAML attribute map supported name-format (see [attribute_map_dir](https://pysaml2.readthedocs.io/en/latest/howto/config.html#attribute-map-dir))                                             |
| SAML_ATTRIBUTES_MAP_UID         | SAML attribute mapping to uid                                                                                                                                                                |
| SAML_ATTRIBUTES_MAP_UID_FIELD   | SAML attribute mapping uid field name                                                                                                                                                        |
| SAML_ATTRIBUTES_MAP_EMAIL       | SAML attribute mapping to email                                                                                                                                                              |
| SAML_ATTRIBUTES_MAP_EMAIL_FIELD | SAML attribute mapping email field name                                                                                                                                                      |
| SAML_ATTRIBUTES_MAP_CN          | SAML attribute mapping to common name                                                                                                                                                        |
| SAML_ATTRIBUTES_MAP_CN_FIELD    | SAML attribute mapping common name field name                                                                                                                                                |
| SAML_ATTRIBUTES_MAP_SN          | SAML attribute mapping to surname                                                                                                                                                            |
| SAML_ATTRIBUTES_MAP_SN_FIELD    | SAML attribute mapping surname field name                                                                                                                                                    |
| SAML_DJANGO_USER_MAIN_ATTRIBUTE | Django field to use to find user and create session (see [user attributes and account linking](https://djangosaml2.readthedocs.io/contents/setup.html#users-attributes-and-account-linking)) |
| SAML_USE_NAME_ID_AS_USERNAME    | Use SAML2 name id as username (see [user attributes and account linking](https://djangosaml2.readthedocs.io/contents/setup.html#users-attributes-and-account-linking))                       |
| SAML_CREATE_UNKNOWN_USER        | Create user if not found in Django database (see [user attributes and account linking](https://djangosaml2.readthedocs.io/contents/setup.html#users-attributes-and-account-linking))         |
| SAML_KEY_FILE                   | Path to private key (see [key_file](https://pysaml2.readthedocs.io/en/latest/howto/config.html#key-file))                                                                                    |
| SAML_CERT_FILE                  | Path to the public key (see [cert_file](https://pysaml2.readthedocs.io/en/latest/howto/config.html#cert-file))                                                                               |
| SAML_METADATA_REMOTE_URL        | Url to remote SAML metadata file (see [metadata](https://pysaml2.readthedocs.io/en/latest/howto/config.html#metadata))                                                                       |
| SAML_METADATA_REMOTE_CERT       | (Optional) Certificate for the remote (see [metadata](https://pysaml2.readthedocs.io/en/latest/howto/config.html#metadata))                                                                  |
| SAML_METADATA_LOCAL             | Path to local SAML metadata file (see [metadata](https://pysaml2.readthedocs.io/en/latest/howto/config.html#metadata))                                                                       |
| SAML_XMLSEC_BIN_PATH            | Full path to xmlsec1 binary program (see [xmlsec_binary](https://pysaml2.readthedocs.io/en/latest/howto/config.html#xmlsec-binary))                                                          |
| SAML_WANT_RESPONSE_SIGNED       | Set to `True` if responses must be signed (see [want_response_signed](https://pysaml2.readthedocs.io/en/latest/howto/config.html#want-response-signed))                                      |
| SAML_WANT_ASSERTIONS_SIGNED     | Set to `True` if assertions must be signed  (see [want_assertions_signed](https://pysaml2.readthedocs.io/en/latest/howto/config.html#want-assertions-signed))                                |
| SAML_LOGOUT_REQUESTS_SIGNED     | Set to `True` if logout requests must be signed  (see [logout_requests_signed](https://pysaml2.readthedocs.io/en/latest/howto/config.html#logout-requests-signed))                           |
| SAML_LOGOUT_RESPONSES_SIGNED    | Set to `True` if logout responses must be signed  (see [logout_responses_signed](https://pysaml2.readthedocs.io/en/latest/howto/config.html#logout-responses-signed))                        |
| SAML_SIGNING_ALGORITHM          | Signing algorithm  (see [signing_algorithm](https://pysaml2.readthedocs.io/en/latest/howto/config.html#signing-algorithm))                                                                   |
| SAML_DIGEST_ALGORITHM           | Digest algorithm  (see [digest_algorithm](https://pysaml2.readthedocs.io/en/latest/howto/config.html#digest-algorithm))                                                                      |
| CONTACT_PERSON_N                | Contact information for person N (see [contact_person](https://pysaml2.readthedocs.io/en/latest/howto/config.html#contact-person))                                                           |
| ORGANIZATION_NAME_N             | Organization name N (see [organization](https://pysaml2.readthedocs.io/en/latest/howto/config.html#organization))                                                                            |
| ORGANIZATION_DISPLAY_NAME_N     | Organization display name N (see [organization](https://pysaml2.readthedocs.io/en/latest/howto/config.html#organization))                                                                    |
| ORGANIZATION_URL_N              | Organization url N (see [organization](https://pysaml2.readthedocs.io/en/latest/howto/config.html#organization))                                                                             |

#### 2.2.1: SAML Contact Person and Organization environment variables

Environment variables ending with suffix `_N` (see `./deploy/saml2/.env.example`) expect `N` to be a sequence of
integers starting at `1`.  For example, if two contact persons need to be added to the SAML configuration, the following
variables should be set:

```
CONTACT_PERSON_1=
CONTACT_PERSON_2=
```

1. Contact Person

The `CONTACT_PERSON_N` environment variable expects a comma separated list of values in the following order:
- given name,
- surname,
- company,
- email address,
- type (technical, support, administrative, billing or other).

For example:
```
CONTACT_PERSON_1=Ernst,Ruska,TU Berlin,ernst.ruska@example.com,technical
```

2. Organization

Each section of the SAML organization configuration is stored in a separate environment variable. Each variable 
expects a comma separated pair composed of:

- label,
- language code.

Below is an example from the 
[`pysaml2` documentation](https://pysaml2.readthedocs.io/en/latest/howto/config.html#organization) and how to represent
it in the CDCS using environment variables.

Example from the [documentation](https://pysaml2.readthedocs.io/en/latest/howto/config.html#organization):
```
"organization": {
    "name": [
        ("Example Company", "en"),
        ("Exempel AB", "se")
    ],
    "display_name": ["Exempel AB"],
    "url": [
        ("http://example.com", "en"),
        ("http://exempel.se", "se"),
    ],
}
```

Equivalent CDCS (NexusLIMS) configuration using environment variables in `./deploy/saml2/.env`:
```
ORGANIZATION_NAME_1=Example Company,en
ORGANIZATION_NAME_2=Exempel AB,se
ORGANIZATION_DISPLAY_NAME_1=Exempel AB,se
ORGANIZATION_URL_1=http://example.com,en
ORGANIZATION_URL_2=http://exemple.se,se
```

### 2.3: (optional) Handle Server configuration for persistent identifiers (PIDs)

The CDCS platform on which NexusLIMS is based supports the assignment of persistent identifiers (PID) to each record 
that is created or uploaded into the system. By default, the application uses an internal "local" PID to generate 
persistent URLs that can be used to access individual records. This is sufficient for most applications, but 
some users may wish to use an external "[handle server](https://en.wikipedia.org/wiki/Handle_System)" which can assign 
"handles" (a type of PID) to individual records, which will be of the form `20.1000/100`. This will allow you to access
NexusLIMS records by visiting the handle URL, which will be resolved by the CDCS platform and point the browser to the
corresponding experimental record.

To use a handle server, you will need information about your assigned prefix and the username and secret key that are
authorized to create handles under that prefix. To configure NexusLIMS to use handles, modify the environment file
present at `./deploy/handle/.env`, using the `./deploy/handle/.env.example` file as an example (much like how the SAML
integration is configured). The variables that you can configure for handle integration are described in the following
table:

| Variable                            | Description                                                                                                                                                                                                                                                                                                                               |
|-------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `ENABLE_HANDLE_PID`                 | Controls whether NexusLIMS will attempt to use a handle server for PIDs. If so, all the values below should be set to values specific for your handle server config (contact your handle server administrator for any help). If you enable Handle integration but don't set these values correctly; it's _very_ likely things won't work. |
| `HANDLE_NET_URL`                    | The URL of the handle server (e.g. `https://hdl.handle.net`)                                                                                                                                                                                                                                                                              |
| `HANDLE_NET_PREFIX`                 | The handle prefix to use when creating handles NexusLIMS records                                                                                                                                                                                                                                                                          |
| `HANDLE_NET_USER`                   | Handle server authentication for a user that has admin rights to list and create handles on the provided prefix. The value provided here will be encoded as `300:{HANDLE_NET_PREFIX}/{HANDLE_NET_USER}` when it is sent to the handle server, so this value should be just the suffix of the admin handle                                 |
| `HANDLE_NET_SECRET_KEY`             | The "secret key" for the admin user specified above. This should be provided as plain text and not encoded in any way. This value corresponds to the secret key that would be used if you were creating a handle via batch file                                                                                                           |
| `PID_XPATH`                         | The location in the default schema in which to store and search for PID values. Should be provided in "dot" notation, with attributes indicated using the "@" character. The default `PID_XPATH` value of `Experiment.@pid` is required for the integration to work with the [Nexus Experiment](https://doi.org/10.18434/M32245) schema   |
| `AUTO_SET_PID`                      | Whether to auto-create PIDs for records that are curated or uploaded without them. Should likely be True if you're using PIDs at all                                                                                                                                                                                                      |
| `HANDLE_NET_RECORD_INDEX`           | Starting index for records when minting handles (default: 1)                                                                                                                                                                                                                                                                              |
|                                     | _The following values are admin settings for the handle config. The default values are probably fine, but they should match any example batch files you have for creating handles on your handle server_                                                                                                                                  |
| `HANDLE_NET_ADMIN_INDEX`            | The admin index value (default: `100`)                                                                                                                                                                                                                                                                                                    |
| `HANDLE_NET_ADMIN_TYPE`             | The admin type (default: `HS_ADMIN`)                                                                                                                                                                                                                                                                                                      |
| `HANDLE_NET_ADMIN_DATA_FORMAT`      | The admin data format (default: `admin`)                                                                                                                                                                                                                                                                                                  |
| `HANDLE_NET_ADMIN_DATA_INDEX`       | The admin data index value (default: `200`)                                                                                                                                                                                                                                                                                               |
| `HANDLE_NET_ADMIN_DATA_PERMISSIONS` | The admin data permissions (default: `011111110011`)                                                                                                                                                                                                                                                                                      |


### 2.4 (optional) Configure other application settings - *advanced*

This section should not be needed for a basic installation of NexusLIMS, but if you desire, you can modify the
settings used by the underlying CDCS platform to adjust certain other behaviors. (Note, these instructions are 
reproduced essentially unchanged from the [CDCS ones](https://github.com/usnistgov/cdcs-docker#settings) and have 
not been thoroughly tested, but should generally work).

This is accomplished by mounting additional settings files into the deployed containers. By default, the NexusLIMS
repository is configured to use the settings included in the Docker image built in the previous steps (which is 
defined in the 
[NexusLIMS CDCS repository](https://github.com/usnistgov/nexuslims-cdcs/blob/NexusLIMS_master/mdcs/settings.py)).
Alternatively, you can follow the process described below to customize the default settings from the NexusLIMS image.
This can be done to provide settings specific to your production configuration without having to modify files in the
underlying NexusLIMS repository:

- Create a `custom_settings.py` file (see `./deploy/cdcs/ci_settings.py` or `./deploy/cdcs/test_settings.py` 
  as examples),
- Set the `SETTINGS` variable in `./deploy/.env` to `custom_settings`, or whatever you named the file (without the 
  `.py` extension)
- Uncomment the line in the `cdcs/volumes` section of `./deploy/docker-compose.yml` that looks like:
  `- ./cdcs/${SETTINGS}.py:/srv/curator/${PROJECT_NAME}/${SETTINGS}.py`. This will instruct Docker to mount the file
  specified in `./deploy/cdcs/${SETTINGS}.py` into the resulting Docker container, and any changes you make to this
  local file will be reflected when the container is restarted.

The [`DJANGO_SETTINGS_MODULE`](https://docs.djangoproject.com/en/2.2/topics/settings/#envvar-DJANGO_SETTINGS_MODULE)
environment variable can be set to select which settings to use. By default, the `docker-compose.yml` file sets it using
the values of `PROJECT_NAME` and `SETTINGS` variables.

For more information about production deployment of a Django project, please check the 
[Deployment Checklist](https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/#deployment-checklist)

## Step 3: Run the NexusLIMS CDCS application

To start the NexusLIMS application (and the supporting services), use the `docker-compose up -d` command. This will 
download the supporting images as needed, start all the required containers, and detach (because of the `-d` option),
returning you to the command line. If the `-d` option is not given, the Docker processes will stay in the foreground
and the application will stop when the terminal is closed or you interrupt it using `Ctrl-C`.

``` bash
$ docker-compose up -d
```

To view the logs for the entire "stack" (the collection of containers), you can use Docker Compose's log command. Adding
the `--follow` option will "follow" the logs and they will be printed to the terminal as they are generated (press 
`Ctrl-C` to stop following the logs)

```bash
$ docker-compose logs --follow
```

(Optional) For testing purposes, if you want to try using the HTTPS protocol (and you set the `SERVER_CONF` and 
`SERVER_URI` values appropriately), you can then run the following script to generate and copy a self-signed 
certificate to the container:

``` bash
$ ./docker_set_ssl.sh
```

Your browser will warn you about this self-signed certificate the first time you access the application, but you can 
safely ignore the warning during development (note that certain features may not work with the self-signed certificate,
and you should never use a self-signed certificate in production).

If you want to use SSL in production, add your certificate and key file into the `./deploy/nginx/` folder, and uncomment
the appropriate lines from the `curator_nginx/volumes` section of the `./deploy/docker-compose.yml` file to use that 
certificate inside the container.

## Step 4: Create a superuser

You will need to create a "superuser" with administrative privileges to manage things inside the CDCS application. This
will be the main administrator on the platform. Once it has been created, more users can be added using the web 
interface (or automatically via SAML, if that is configured). Wait for the CDCS server to start after running 
`docker-compose up -d`, then run the following, replacing the three `super_X` placeholder values with real ones:

```bash
$ ./docker_createsuperuser.sh super_username super_password super_email
```

## Step 5: Try to access the NexusLIMS application

NexusLIMS should now be available at the `SERVER_URI` set at deployment. 

If not, please check information in the troubleshooting section below.

## Step 6: Stopping the NexusLIMS application

To stop the NexusLIMS CDCS application, use the following Docker Compose command from the `./deploy` folder:

```bash
$ docker-compose down
```

Any data stored in the system should be persisted and be available the next time you run `docker-compose up`.

If you would like to delete the containers and **all the data** stored in the deployed CDCS system, run the `down` 
command with the `-v` flag, which will instruct Docker Compose to delete all the 
[Docker volumes](https://docs.docker.com/storage/volumes/) associated with the application.
**Be warned**, this command will delete **all** data including records, user settings, any self-signed
SSL certificates you copied, etc. The next time you run `docker-compose up`, you will need to recreate
a superuser, etc.:

```
$ docker-compose down -v
```


## Appendix A: Troubleshooting

### Local deployment

**DO NOT** set `HOSTNAME`, `SERVER_URI` and `ALLOWED_HOSTS` to `localhost` or `127.0.0.1`. If you do so, the system
will appear to start properly, but some features will not work (e.g. the search page may show an error instead of
returning data). This is due to the particulars of how Docker sets up IP addresses and how those addresses are routed 
through the application. When deploying locally, use the computer's IP address to set those two
variables, and use the same IP address **when accessing NexusLIMS via a web browser**. i.e. if your machine's IP
address is 192.168.1.3, and the default server configuration was used to deploy the system, access it by typing 
http://192.168.1.13 in the address bar of the browser.

To find the IP of the local machine:
- On Linux and MacOS, run: `ifconfig` or `ip addr show`
- On Windows, run: `ipconfig`

Then update the `.env` file:

```bash
HOSTNAME=xxx.xxx.xxx.xxx
SERVER_URI=http://xxx.xxx.xxx.xxx
ALLOWED_HOSTS=xxx.xxx.xxx.xxx
```

**NOTE:** For testing purposes, `ALLOWED_HOSTS` can be set to `*`:

```bash
ALLOWED_HOSTS=*
```

### Production deployment

- Make sure `SERVER_CONF` is set to `https`
- Update the file `nginx/https.conf` if necessary for any settings particular to your deployment environment
- Have a look at the Django
  [deployment checklist](https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/#deployment-checklist) for
  other considerations

### Examining log files

You can check all the components are running properly by checking their logs. This can be done using either the 
`docker-compose` or `docker` commands

For example, to check the logs of the individual containers using the `docker` command, use the following commands:
```bash
$ docker logs -f mdcs_cdcs
$ docker logs -f mdcs_cdcs_nginx
$ docker logs -f mdcs_cdcs_mongo
$ docker logs -f mdcs_cdcs_postgres
$ docker logs -f mdcs_cdcs_redis
```

Alternatively, from the `./deploy` folder, you can use the `docker-compose` command from before to view all the 
containers' logs at once:

```bash
$ docker-compose logs
```

You can also inspect one container at a time using the name of the "service" as it is defined in the
`docker-compose.yml` file. For example:

```bash
$ docker-compose logs cdcs                # for the main CDCS web application
$ docker-compose logs curator_nginx       # for the Nginx web server
$ docker-compose logs curator_postgres    # for the PostgreSQL server
# etc.
```

### Potential issues with MongoDB RAM usage


From the [MongoDB docker image documentation](https://hub.docker.com/_/mongo):

> By default Mongo will set the wiredTigerCacheSizeGB to a value
proportional to the host's total memory regardless of memory limits
you may have imposed on the container. In such an instance you will
want to set the cache size to something appropriate, taking into
account any other processes you may be running in the container
which would also utilize memory.

Having multiple MongoDB containers on the same machine could be an
issue as each of them will try to use the same amount of RAM
from the host without taking into account the amount used by other
containers. This could lead to the server running out of memory.

### How to fix it?

The amount of RAM used by MongoDB can be restricted by adding the
`--wiredTigerCacheSizeGB` option to the mongodb command in the `curator_mongo` section
of the `docker-compose.yml` file:

**Example:**
```yml
command: "--auth --wiredTigerCacheSizeGB 8"
```

More information on MongoDB RAM usage can be found in the
[documentation](https://docs.mongodb.com/manual/faq/diagnostics/#faq-memory)

## Appendix B: Additional components

Additional components can be added to the NexusLIMS CDCS stack by providing `docker-compose.yml` files for those.
Update the `COMPOSE_FILE` variable in the `.env` file to do so. More information can be found in on this option in the
[documentation](https://docs.docker.com/compose/reference/envvars/#compose_file).

### Elasticsearch

Ongoing developments on the CDCS make use of Elasticsearch. To add Elasticsearch to the CDCS stack, you can do the 
following:

Update the `./deploy/.env` file to deploy Elasticsearch:
```
COMPOSE_FILE=docker-compose.yml:elasticsearch/docker-compose.yml
```

Add and fill the following environment variables:

| Variable        | Description                                      |
|-----------------|--------------------------------------------------|
| ELASTIC_VERSION | Version of the Elasticsearch image (e.g. 7.16.2) |

On linux, you will need to increase the available 
[virtual memory](https://www.elastic.co/guide/en/elasticsearch/reference/7.x/vm-max-map-count.html).

## Appendix C: Other helper scripts included in this repository

Aside from the `docker_create_superuser.sh` and `docker_set_ssl.sh` scripts described previously, there are a few other
scripts provided that accomplish various tasks that may be of interest:

### `docker_rebuild.sh`

This script will completely rebuild the NexusLIMS application and run the commands needed to wipe all data and restart
the application with a superuser with username and password of `admin` and `admin`. This script can be handy during
development to quickly redeploy the entire stack from scratch.

### `docker_update_timestamps.sh`

This script will update the internal "modification time" of all records present in the system according to the value
found at the `acquisitionActivity/startTime` XML node of each record. Since the NexusLIMS search interface displays 
records in the order they were last modified, this script was written to effectively "reorder" the records,
which may no longer be in the expected order after migrating them from one schema to another, or after restoring
from a backup. 

It also demonstrates how to run a Python script _inside_ the running CDCS container that reads the `xml_content` of 
each record and make modifications to the underlying Django database objects.

### `docker_update_xslt.sh`

This script facilitates the process of updating the XSLT documents that define how a given XML record is translated
to the HTML that a user sees on the search or detail page for each record. The XSLT associated with a particular schema
can be updated in the administration panel via the web GUI, but this process quickly becomes tedious if you are making
frequent changes during development.

The script will take files named `list.xsl` and `detail.xsl` in the `./deploy/cdcs` folder and copy them along
with a helper python script  (`update_xslt.py`) into the running CDCS container. It will then use these files to 
find the active template (schema) and update the contents of the existing XSLT files via the Python API.

Like some of the other provided scripts, you will need to provide a superuser's username and password on the command 
line when running it interactively.

### `fix_permissions.sh`

This script is located at the top level of the repository (rather than in the `./build` or `./deploy` folder). It is 
included in case the [`umask`](https://en.wikipedia.org/wiki/Umask) settings on your system are too restrictive. In this
case, if you clone this repository, the "others" permission setting may not be open enough for it to be read by the
Docker containers. This will cause odd permission errors while trying to build or deploy the NexusLIMS code. 
Running the `fix_permissions.sh` script will fix this by adjusting the permissions of each file in 
the directory tree underneath it so that the "others" permission matches the "group" permission. This script only makes 
sense to use on a Linux or Mac host.

## Appendix D: Working with the information in the CDCS database's directly

With care, you can inspect and make changes to the information contained in the CDCS databases (this can be useful
when debugging or during development). The following information was documented during the development of NexusLIMS and
is provided for additional context. It is generally __not recommended__ to mess with the underlying
databases unless you have some specific need and understand that you could completely break things.

There are two primary databases used by CDCS (and by extension, NexusLIMS): the Django application uses PostgreSQL,
while all the data and schemas (called templates by CDCS) are stored in MongoDB.

### PostgreSQL

From the deployment directory, the easiest way to get access to the PostgreSQL database is to run the command:

```bash
$ docker exec -it mdcs_cdcs ./manage.py dbshell
```

This will put you in an interactive [`psql`](https://www.postgresql.org/docs/13/app-psql.html) session connected to the
Django database, which may be easier for poking around than using the Django python interface. A few examples:

#### Showing the database tables:

```bash
cdcs=# \dt
                       List of relations
 Schema |                Name                 | Type  |  Owner
--------+-------------------------------------+-------+---------
 public | auth_group                          | table | curator
 public | auth_group_permissions              | table | curator
 public | auth_permission                     | table | curator
 public | auth_user                           | table | curator
 public | auth_user_groups                    | table | curator
 public | auth_user_user_permissions          | table | curator
 public | captcha_captchastore                | table | curator
 public | core_main_app_main                  | table | curator
 public | defender_accessattempt              | table | curator
 public | django_admin_log                    | table | curator
 public | django_celery_beat_clockedschedule  | table | curator
 public | django_celery_beat_crontabschedule  | table | curator
 public | django_celery_beat_intervalschedule | table | curator
 public | django_celery_beat_periodictask     | table | curator
 public | django_celery_beat_periodictasks    | table | curator
 public | django_celery_beat_solarschedule    | table | curator
 public | django_content_type                 | table | curator
 public | django_migrations                   | table | curator
 public | django_session                      | table | curator
 public | django_site                         | table | curator
 public | oauth2_provider_accesstoken         | table | curator
 public | oauth2_provider_application         | table | curator
 public | oauth2_provider_grant               | table | curator
 public | oauth2_provider_refreshtoken        | table | curator
(24 rows)
```

#### Showing all users:

Note that any users created via SAML single-sign-on will not have password assigned

```bash
cdcs=# SELECT * FROM auth_user;
id |         password           |          last_login           | is_superuser | username | first_name |  last_name   |        email           | is_staff | is_active |         date_joined
---+----------------------------+-------------------------------+--------------+----------+------------+--------------+------------------------+----------+-----------+------------------------------
 1 | pbkdf2_sha256$xxx$xxxx$xx= |                               | t            | super    |            |              |                        | t        | t         | 2021-08-19 19:21:07.84+00
 2 |                            | 2021-11-15 15:48:16.426+00    | f            | uname1   | First Name | Last Name    | email.address@nist.gov | f        | t         | 2021-08-24 17:05:49.557+00
 3 |                            | 2021-11-04 16:13:20.505+00    | f            | uname2   | First Name | Last Name    | email.address@nist.gov | f        | t         | 2021-08-27 14:24:11.487+00
```

#### Making a user an admin:

```bash
cdcs=# UPDATE auth_user SET is_superuser = True, is_staff = True WHERE username = 'username_to_update';
UPDATE 1
```

### MongoDB

To look at the data contained in the application's MongoDB, connect using the `mongo` interface on the mongo Docker 
container (using the `.env` file makes it easier to source the right username and password directly from that file).
Run these commands from the `./deploy/` folder:

```bash
$ source .env; docker-compose exec curator_mongo mongo -u $MONGO_USER -p $MONGO_PASS $MONGO_DB
MongoDB shell version v4.0.3
connecting to: mongodb://127.0.0.1:27017/cdcs
Implicit session: session { "id" : UUID("xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx") }
MongoDB server version: 4.4.13
```

#### View collections (tables)

```
> show collections
account_request
bucket
curate_data_structure
data
exported_compressed_file
exporter
fs_data.chunks
fs_data.files
fs_exporter_compressed_file_collection.chunks
fs_exporter_compressed_file_collection.files
module
oai_data
oai_metadata_format
oai_record
oai_registry
oai_settings
pid_settings
pid_xpath
query
search_operator
template
template_xsl_rendering
version_manager
workspace
xsl_transformation
```

#### Find all "data" created after a certain date:

```
> db.data.find({creation_date: {$gt: ISODate("2021-12-20T00:00:00.000Z")}})
```

#### Same thing, but count number of results instead:

```
> db.data.countDocuments({creation_date: {$gt: ISODate("2021-12-20T00:00:00.000Z")}})
```

#### List the XSL files registered in the system:

```
> db.xsl_transformation.find().pretty()
{
        "_id" : ObjectId("xxxxxxxxxxxxxxxxxxxxxxxx"),
        "_cls" : "XslTransformation",
        "name" : "detail.xsl",
        "filename" : "detail.xsl",
        "content" : "<?xml version=\"1.0\" encoding=\"UTF..."
}
{
        "_id" : ObjectId("xxxxxxxxxxxxxxxxxxxxxxxx"),
        "_cls" : "XslTransformation",
        "name" : "list.xsl",
        "filename" : "list.xsl",
        "content" : "<?xml version=\"1.0\" encoding=\"UTF..."
}
```

#### List all (local) PIDs (if not using handle server integration):
```
> db.local_id.find().pretty()
{
        "_id" : ObjectId("012345678901234567890123"),
        "record_name" : "cdcs/ABCDEFGHIJ012345"
}
{
        "_id" : ObjectId("012345678901234567890124"),
        "record_name" : "cdcs/ABCDEFGHIJ012346"
}
{
        "_id" : ObjectId("012345678901234567890125"),
        "record_name" : "cdcs/ABCDEFGHIJ012347"
}
{
        "_id" : ObjectId("0123456789012345678901236"),
        "record_name" : "cdcs/ABCDEFGHIJ012348"
}
...
```

#### Delete a (local) PID (if not using handle server integration):

```
> db.local_id.deleteMany({"record_object_id":"012345678901234567890123"})
{ "acknowledged" : true, "deletedCount" : 2 }
```

#### Delete all PIDs (if not using handle server integration):

```
> db.local_id.deleteMany({})
{ "acknowledged" : true, "deletedCount" : 364 }
```

# Disclaimer

[NIST Disclaimer](https://www.nist.gov/disclaimer)
