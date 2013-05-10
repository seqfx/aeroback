Aeroback
========
Migrate/backup your data to Amazon S3 and Google Storage
--------------------------------------------------------
Backup or move your server data or desktop files to Amazon S3 or Google Storage. This Python 2.7 script is easily configurable and supports compressed and incremental directory backup/migration to cloud storages.

Why this script?
----------------
My server has accumulated a lot of GB of data that I needed to store long term. However, the problem was my server's monthly bandwidth allowance which I couldn't exceed.

**Aeroback migrates data in instalments that you control.** This allows for a gradual transition to the cloud storage while keeping your server running and receiving new data.

###Main features:
* Set limit of upload amount per session
* Neatly organizes several machines' backups in the same storage bucket
* Easily configurable via simple `.ini` files
* Recognizes machine it is being run on (all configs are in one location)
* Emails detailed report when done (optional)

###Supported backup types:
* Incremental directories with includes/excludes and max upload limit
* Compressed directories with history of N versions
* Database backup (MongoDB and MySQL) with history on N versions

###Supported cloud storages:
* Amazon S3
* Google Storage

Example of incremental files backup
-----------------------------------
This is the main cause for writing this script. Specify a directory, its optional include/exclude subdirectories and set a limit of upload per session.
For example:
```
[backup_dir_increment]
    active = true
    dirstorage = data/sound
    dir = /home/alex/data/sound
    maxupload = 100M
    includes =
    excludes = 
            work/temp
            cache
    description = Audio files
```
To limit upload set `maxupload`. The format is g or G for gigabytes (`5g`), m or M for megabytes (`5M`), k or K for kilobytes (`5k`), or one can use all digits like `314159265359`.

Dependencies & trying Aeroback without installing gsutil
--------------------------------------------------------

Only two dependencies:
* **SQLite** database engine
* **gsutil** for Amazon S3 and Google Storage access

Aeroback uses SQLite database engine which is normally present on most machines. If not, read [SQLite site](http://sqlite.org/) about how to get one.

External command `gsutil` needs to be present to access Amazon S3 and Google Storage. Read [gsutil project page](https://developers.google.com/storage/docs/gsutil) for more details.

But there is no need to install and configure `gsutil` to get a feel how Aeroback works. Skip next section "How to install gstuil" and proceed to Aeroback installation and configuration. When done, run Aeroback in dry mode:
```
<aeroback_install_dir>/aeroback/aeroback.py -dry
```
It will do all necessarily operations except for actually storing data to the storage. A very handy option to test before configuring further.

How to install gsutil
---------------------
###Install gsutil
[Follow this guide](https://developers.google.com/storage/docs/gsutil_install) to install `gsutil`.

###Configure gsutil
Execute 
```
gsutil config
```
and enter your Google Storage credentials. To authenticate to Amazon S3, simply edit `<your_homedir>/.boto` file and add credentials in these sections:
```ini
[Credentials]
...
gs_access_key_id = <your google access key ID>
gs_secret_access_key = <your google secret access key>
...
aws_access_key_id = <your key id>
aws_secret_access_key = <your access key>
```
Optionally, add `gsutil` to your system `PATH` or skip this step and set gsutil location in the Aeroback configuration file (easier for a server running Aeroback as a cron job).

How to install Aeroback
-----------------------
###Get Aeroback
Checkout aeroback somewhere on your disk and make the script executable
```
mkdir <aeroback_install_dir>
cd <aeroback_install_dir>
git clone https://github.com/seqfx/aeroback.git
chmod +x aeroback/aeroback.py
```

How to Configure Backup
-----------------------
Configuration files are located in `aeroback.config` directory. 

Initially the config directory only has `EXAMPLES` subdirectory. Your need to use those examples to create your config files **inside `aeroback.config` directory**:
* `notify-email.ini` with your email settings
* at least one `<filename>.ini` with backup settings

**If any of these files files are absent the script will complain and will not run.**

`aeroback.config` is the place to put configuration files for one or several machines. Aeroback will execute only relevant configurations. This approach makes it easier to setup several machine backups. For example, one for your development box and another for a server.

Each setup is an `.ini` file usually following this naming convention `_home_<your_username>.ini`.
*Important: * to ignore some config files prepend their name with `OFF`, for example `OFF_home_ben.ini`.
Aeroback recognizes machine by a presence of a relevant directory that is specified in each config file:
```
[identity]
    dir = /home/alex
    gsutil = /home/alex/gsutil
```
Also, it's a good place to specify the location of `gsutil` on that particular machine. If left unspecified `gsutil =` then Aeroback assumes that `gsutil` is on your system `PATH`.

To configure storages edit these sections:
```
[storage_amazons3]
    active = true             
    bucket = <your_bucket>
    dirstorage = <home_dir_inside_bucket>
 
[storage_googlestorage]
    active = false
    bucket = <your_bucket>
    dirstorage = <home_dir_inside_bucket>
```
`dirstorage` is useful for separating several machine backups inside single bucket.
Aeroback accepts single storage or both storages used for duplicating backup.

How to Configure Email Notifications
------------------------------------
Aeroback will send you a detailed report after each run. While this is optional it's a good idea to have it active while you fine tune the backup settings. All errors will be reflected in the report.
Email configuration looks like so:
```
[identities]
     dirs = /home/alex, /home/alex_server
 
 [email:*]
     active = true
     smtp_server = alex_server.com
     smtp_port = 25
     user = alex@alex_server.com
     password = secret
     from = alex@alex_server.com
     to = alex@alex_server.com
     subject = Aeroback       
    
 [email:/home/alex]
     active = false            
     smtp_server =
     smtp_port =               
     user = 
     password =                
     from = 
     to =                      
     subject = Backup: alex
    
 [email:/home/alex_server]
     active = true             
     smtp_server =             
     smtp_port =               
     user = 
     password = 
     from = 
     to = 
     subject = Backup: alex_server
```
`[identities]` contain list of identifying directories for different machines.

`[email:*]` is the master setup which will be applied to every machine provided there will be no further overriding

`[email:<identity_dir>]` is where any of master parameters can be overriden. In the example above, the local machine identified by `/home/ales` has `active = false` which turns off email sending. The server identified by `/home/alex_server` has `active = true` and will be sending Aeroback emails on completion.

How to Run
----------
####Manually
Execute shell command 
```
<your_homedir>/aeroback/aeroback/aeroback.py
```
####As a cron job
Edit cron file via `crontab -e` and add
```
# Backup via Aeroback
0 */8 * * * <your_homedir>/aeroback/aeroback/aeroback.py
```
This example will run Aeroback every 8 hours.

Controlling backup execution frequency
--------------------------------------
Each backup can have an optional `frequency` parameter that designates minimum period since last execution of that particular backup type after which the backup may be executed again. To put it simpler, how often you want this backup to run.

Accepted values are hours and minutes separated by `h` or `H`. For example, `0h15`, `1h00`, `3h15`, `4h` or even `120` (for minutes only) are all valid values.

This option allows for finer granularity. You may want your MongoDB backups to run every 4h, while incremental backup needs to run every hour. Achieve this by setting `frequency` option for each backup type and set crontab to the smallest slice of time. 

**Important: Aeroback will not run if previous backup hasn't finished.** It makes sense to use shorter crontab intervals like `0 */1 * * *` meaning run each hour. This way the script will try again in one hour.


Detailed Configuration guide
----------------------------
A more detailed information about each configuration section.

####Machine identifier
Matches configuration file to a specific machine. Example:
```
[identity]
    dir = /home/alex
    gsutil = /home/alex/gsutil
```
`dir` must be present on local drive to match this configuration file

`gsutil` specifies location of `gsutil` if that hasn't been set in system `PATH` variable

####Storages
One or two storages can be used simultaneously. Example:
```
[storage_amazons3]
    active = true
    bucket = <your_bucket>
    dirstorage = <home_dir_inside_bucket>

[storage_googlestorage]
    active = false
    bucket = <your_bucket>
    dirstorage = <home_dir_inside_bucket>
```
`active` turns particular storage backup on/off

`bucket` is the bucket name inside a storage

`dirstorage` is a directory inside the bucket. Highly recommended to have different directories for different machines.

####Incremental Files Backup
**This configuration section can be repeated several times for different directories.** Incrementally uploads all new/changed files to storage. Example:
```
[backup_dir_increment]
    active = true
    dirstorage = data/sound
    dir = /home/alex/data/sound
    maxupload = 500m
    includes =
    excludes = 
          work/temp
          cache
    description = Audio files
```
`active` turns backup on/off

`dirstorage` is a directory inside `<storage_bucket>/<storage_dirstorage>` specified in `[storage_*]` sections

`dir` is a backup directory on local disk

`maxupload` limits upload amount per session. The format is g or G for gigabytes (`5g`), m or M for megabytes (`5M`), k or K for kilobytes (`5k`), or one can use all digits like `314159265359`.

`includes` is a list of subdirectories to include in backup. **Important:** includes always overrides following excludes; meaning if at least one include is provided then no excludes will be take into account.

`excludes` is a list of subdirectories to exclude from backup. Only considered if `includes` list is empty

`description` is a free text, not currently used anywhere

Temporary files and directories are skipped during incremental backup. Currently the script skips files like: `.hello.txt`, `~hello.txt` and `hello.txt~`. Flexible regex configuration for each backup will be added very soon. Stay tuned.

Compressed Directory Backup
---------------------------
**This configuration section can be repeated several times for different directories.** A single directory or multiple directories gets compressed and time stamp added. Handy for keeping a history of multiple versions. For example:
```
[backup_dir_compress]         
    active = true
    dirstorage = emails
    history = 10
    dirs =  
          /home/alex/emails/in
          /home/alex/emails/out
    description = 
```
`active` turns backup on/off

`dirstorage` is a directory inside `<storage_bucket>/<storage_dirstorage>` specified in `[storage_*]` sections

`history` is a number of older versions to be kept (integer). If no history provided then ALL versions will be preserved.

`dirs` is a list of backup directories on local disk to be compressed together in a single archive (.tar.gz)

`description` is a free text that will become the name of the archive

MongoDB and MySQL DB Backups
----------------------------
Data base dump that is compressed and time stamp added. Currently dumps ALL tables.
For example:
```
[backup_db_mongo]             
   active = true
   dirstorage = db/mongo
   history = 5
   user = 
   password =
   host = 127.0.0.1
   description = DB Mongo backup

[backup_db_mysql]
   active = true
   dirstorage = db/mysql
   history = 8
   user = 
   password =
   host = 127.0.0.1
   description = DB MySQL backup
```
`active` turns backup on/off

`dirstorage` is a directory inside `<storage_bucket>/<storage_dirstorage>` specified in `[storage_*]` sections

`history` is a number of older versions to be kept (integer). If no history provided then ALL versions will be preserved.

`user`, `password`, `host` are standard DB connection parameters

`description` is a free text, not currently used anywhere

Aeroback .work directory
------------------------
This is a directory automatically created inside the `aeroback` folder. It contains:
* `log` directory where last N of plain text logs stored
* `diag` directory where last log formatted as HTML is stored
* `temp` directory that the script uses for its work (creating zipped files, etc.)
* `runlog.ini` file where the latest executions are logged along with times

Development options
-------------------
###Dry mode
Aeroback can be run in a 'dry' mode meaning no actual data will be send to/from the storages. It's a good way to test that your configuration is working before attempting to send any data. Run the script with `-dry` option:
`<your_homedir>/aeroback/aeroback/aeroback.py -dry`

###Finer configuration
File `core.ini` contains some settings that you can change:
* locations of `aeroback.config` and `aeroback.work` directories
* number of historical versions for log files

###If Aeroback refuses to run
This may happen if previous run did not clear its `running` flag. In this case either delete or manually edit file `aeroback.work/runlog.ini` and change all `running = True` to `running = False`. For example:
```ini
[app]
running = False
last_run = Fri May 10 12:52:09 2013

[dir_increment:data/video]
running = False
last_run = Thu May 09 22:18:57 2013

[dir_increment:data/audio]
running = False
last_run = Thu May 09 22:54:16 2013

[db_mongo:mongo]
running = False
last_run = Fri May 10 09:11:36 2013
```

The End
-------
