# YAFFS-Forensics

A Python script to extract information for a YAFFS file system

This can:
- [x] Read the different files
- [x] Reconstruct file tree structure
- [x] Display Metadata
    - [x] Type of object
    - [x] Size of file and directories
    - [x] Last time read/modified


## Prerequisites

- **Python** ≥ 3.9
- **pip** ≥ 22.0.4

## Installation

Clone the repo 
```bash
git clone https://github.com/SA8cho/YAFFS-Forensics.git
```


Install the packages using the package manager [pip](https://pip.pypa.io/en/stable/)
```bash
pip install -r requirements.txt
```


## Usage

```python
# returns 'words'
foobar.pluralize('word')

# returns 'geese'
foobar.pluralize('goose')

# returns 'phenomenon'
foobar.singularize('phenomena')
```

Example with the provided file
```bash
.root/
├── docs/ [type=dir mode=0755 uid=1000 gid=1000 atime=2025-06-03T17:14:30 mtime=2025-06-03T17:14:30 ctime=2025-06-03T17:14:30]
│   ├── manual.txt [type=file size=49 mode=0644 uid=1000 gid=1000 atime=2025-06-03T17:13:58 mtime=2025-06-03T17:13:58 ctime=2025-06-03T17:13:58]
│   └── Version.txt [type=file size=42 mode=0644 uid=1000 gid=1000 atime=2025-06-03T17:14:30 mtime=2025-06-03T17:14:30 ctime=2025-06-03T17:14:30]
├── misc/ [type=dir mode=0755 uid=1000 gid=1000 atime=2025-06-03T17:18:12 mtime=2025-06-03T17:18:12 ctime=2025-06-03T17:18:12]
│   └── data.json [type=file size=49 mode=0644 uid=1000 gid=1000 atime=2025-06-03T17:18:12 mtime=2025-06-03T17:18:12 ctime=2025-06-03T17:18:12]
├── pictures/ [type=dir mode=0755 uid=1000 gid=1000 atime=2025-06-03T17:10:52 mtime=2025-06-03T17:11:34 ctime=2025-06-03T17:11:34]
│   ├── img1.jpeg [type=file size=8211 mode=0644 uid=1000 gid=1000 atime=2025-06-03T17:10:52 mtime=2025-06-03T17:10:07 ctime=2025-06-03T17:10:52]
│   └── img2.jpg [type=file size=42061 mode=0644 uid=1000 gid=1000 atime=2025-06-03T17:11:34 mtime=2025-06-03T17:11:34 ctime=2025-06-03T17:11:34]
└── secret.txt [type=file size=43 mode=0644 uid=1000 gid=1000 atime=2025-06-03T17:20:06 mtime=2025-06-03T17:20:06 ctime=2025-06-03T17:20:06]
```

## License

[MIT](https://choosealicense.com/licenses/mit/)
