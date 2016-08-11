# Tag Search

Simple GTK application to tag and browse files.

## Requirements

- Python3
- Gtk

## Browser

To browse the tagged files use
```sh
./browser.py
```

![input](https://raw.githubusercontent.com/fdibaldassarre/tag-search/master/pictures/browser.jpg)

## Tag file

To tag a file use
```sh
./tag-file.py path/to/file
```

![input](https://raw.githubusercontent.com/fdibaldassarre/tag-search/master/pictures/tag.jpg)

## Add file to root folder

Alternatively if you want to keep all your tagged files in a certain folder
(root folder under configuration) use
```sh
./add-file.py path/to/file
```

![input](https://raw.githubusercontent.com/fdibaldassarre/tag-search/master/pictures/add_file_base.jpg)

This command will move the selected file under the root folder specified in the configuration.
The window can be customized (not very easily at the moment). See the file examples/create_add_file_layout.py.

![input](https://raw.githubusercontent.com/fdibaldassarre/tag-search/master/pictures/add_file_adv.jpg)

## Profiles

The program supports profiles. Launch the browser, tag_file and add_file with the flag
```sh
--profile profile_name
```
to create/use a different profile.

## TODO

Filter files by mimetype

Easier customization of Add File window
