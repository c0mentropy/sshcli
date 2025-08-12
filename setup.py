from setuptools import find_packages, setup

sshcli_version = "1.0.6"
sshcli_author = "Comentropy Ckyan"
sshcli_author_email = "comentropy@foxmail.com"
sshcli_git_url = "https://github.com/c0mentropy/sshcli.git"
sshcli_description = "Asynchronous batch attack based on ssh connection"

setup(
    name="sshcli",
    version=f"{sshcli_version}",
    author=f"{sshcli_author}",
    author_email=f"{sshcli_author_email}",
    description=f"{sshcli_description}",
    packages=find_packages(),
    package_data={
        'sshcli': ['sshcli/conf/*', '.assets/*', 'README-EN.md', 'VERSION.md', 'TODO.md'],
    },
    include_package_data=True,
    install_requires=["click", "asyncssh", "aioconsole", "colorlog", "prompt_toolkit", "pyyaml"],
    entry_points="""
        [console_scripts]
        sshcli=sshcli.cli:cli
    """,
    url=f"{sshcli_git_url}",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: CC-BY-4.0"
    ],
)
