Aeroback
========
Backup/migrate your data to Amazon S3/Google Storage
----------------------------------------------------
Backup or move your server data or desktop files to Amazon S3 or Google Storage. This Python 2.7 script is easily configurable and supports compressed and incremental directory backup/migration to cloud storages.

Why this script?
----------------
My server has accumulated a lot of GB of data that I needed to store long term. However, the problem was my server's monthly bandwidth allowance which I couldn't exceed. 
Aeroback migrates data in installments that you control. This allows for a gradual transition to the cloud storage while keeping your server running and receiving new data.

###Main features:
* Set limit of upload amount per session
* Neatly organizes several machines' backups in the same bucket
* Easily configurable via simple .ini file
* Recognizes machine it is being run on
* Emails detailed report when done (optional)

###Supported backup types:
* Incremental directories with includes/excludes and max upload limit
* Compressed directories with history of N versions
* Database backup (MongoDB and MySQL) with history on N versions

###Supported cloud storages:
* Amazon S3
* Google Storage

Incremental Files Backup
------------------------
This is the main cause for writing this script. Specify a directory, its optional include/exclude subdirectories and set a limit of upload per session.
For example:
```
[backup_dir_increment]
    active = true
    dirstorage = data/sound
    dir = /home/alex/data/sound
    maxupload = 1g
    includes =
    excludes = 
          work/temp
          cache
    description = Audio files
```
To limit upload set `maxupload`. The format is g or G for gigabytes (`5g`), m or M for megabytes (`5M`), k or K for kilobytes (`5k`), or one can use all digits like `314159265359`.

Compressed Directory Backup
---------------------------
A single directory or multpiple directories gets compressed and time stamp added. Handy for keeping a history of multiple versions.
For example:
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

Mongo DB Backup
---------------
Data base dump that is compressed and time stamp added. Also supports for a history of versions. Currently dumps ALL tables.
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
```

MySQL DB Backup
---------------
Data base dump that is compressed and time stamp added. Also supports for a history of versions. Currently dumps ALL tables.
For example:
```
[backup_db_mysql]
   active = true
   dirstorage = db/mysql
   history = 8
   user = 
   password =
   host = 127.0.0.1
   description = DB MySQL backup
```

Dependencies
------------
External command `gsutil` needs to be present to access Amazon S3 and Google Storage. Read [gsutil project page](https://developers.google.com/storage/docs/gsutil) for more details.

How to Install
--------------
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

###Get Aeroback
Checkout aeroback somewhere on your disk with 
```
git clone https://github.com/seqfx/aeroback.git
```

How to Configure Backup
-----------------------
Configuration files are located in `aeroback.config` folder. Configuration for multiple machines can be stored there making it easier to setup (for example) two backups: one for your development box and another for a server.
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
`[identities]` contain list of idenitifying directories for different machines.
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
# Backup via AeroBack
0 */8 * * * <your_homedir>/aeroback/aeroback/aeroback.py
```
This example will run Aeroback every 8 hours.

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
*This section can be repeated several times for different directories*
Incrementally uploads all new/changed files to storage. Example:
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
`dirstorage` is a directory inside `<storage_bucket>/<storage_dirstorage>` speficied in `[storage_*]` sections
`dir` is a backup directory on local disk
`maxupload` limits upload amount per session. The format is g or G for gigabytes (`5g`), m or M for megabytes (`5M`), k or K for kilobytes (`5k`), or one can use all digits like `314159265359`.
`includes` is a list of subdirectories to include in backup. *Important:* includes always overrides following excludes; meaning if at least one include is provided then no excludes will be take into account.
`excludes` is a list of subdirectories to exclude from backup. Only considered if `includes` list is empty
`description` is a free text, not currently used anywhere

Compressed Directory Backup
---------------------------
A single directory or multpiple directories gets compressed and time stamp added. Handy for keeping a history of multiple versions. For example:
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
`dirstorage` is a directory inside `<storage_bucket>/<storage_dirstorage>` speficied in `[storage_*]` sections
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
`dirstorage` is a directory inside `<storage_bucket>/<storage_dirstorage>` speficied in `[storage_*]` sections
`history` is a number of older versions to be kept (integer). If no history provided then ALL versions will be preserved.
`user`, `password`, `host` are standard DB connection parameters
`description` is a free text, not currently used anywhere

The End
-------
