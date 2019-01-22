#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from pathlib import Path
import requests
import tempfile
import tarfile
import subprocess
import shutil
import os, sys
import logging

class ESolcType:

    static_linux = "solc-static-linux"
    source = "solidity_%(version)s.tar.gz"
    javascript = "soljson.js"


class SolcWrapper(object):

    SOLC_DOWNLOAD_URL = "https://github.com/ethereum/solidity/releases/download/v%(version)s/%(type)s"

    def __init__(self, path="/usr/local/bin/", argv=None):
        self._solc_directory = Path(path)
        if not self._solc_directory.is_dir():
            self._solc_directory.mkdir()

        self._args, self._solc_args = self.parse_args(argv)

    @property
    def args(self):
        return self._args

    @staticmethod
    def get_url(version, _type):
        return SolcWrapper.SOLC_DOWNLOAD_URL % {"version":version, "type": _type % {"version":version}}

    def list(self, version="*"):
        """
        list available versions of solc
        :return:
        """
        if version in (True, None):
            version = "*"
        return {path.name.split("-",1)[1]:path for path in self._solc_directory.glob("./solc-%s"%version)}

    def list_sorted(self, version="*"):
        d = self.list(version=version)
        keys = list(d.keys())
        keys.sort(key=lambda s: [int(u) for u in s.split('.')])
        return [(v,d[v]) for v in reversed(keys)]

    def is_available(self, version):
        """
        checks if a given version of solc is already installed

        :param version:
        :return:
        """
        return bool(self.list(version=version))

    def install(self, version, _type):
        assert(_type in (ESolcType.static_linux, ESolcType.source, ESolcType.javascript))

        with tempfile.NamedTemporaryFile(mode="w+b") as f_tmp:
            logging.debug(f_tmp.name)

            url = SolcWrapper.get_url(version=version, _type=_type)
            logging.info("downloading %s"%url)
            SolcWrapper.download_file(url=url, f_destination=f_tmp.file)

            if _type in (ESolcType.source,):
                logging.debug("is archive")
                with tempfile.TemporaryDirectory() as tmp_dir:
                    p_tmp_dir = Path(tmp_dir)
                    logging.debug("tempdir: %s" % tmp_dir)
                    archive = tarfile.open(f_tmp.name, mode="r:gz")
                    archive.extractall(tmp_dir)
                    logging.info("archive decompressed")
                    subdir = list(p_tmp_dir.glob("solidity*"))
                    logging.debug(subdir)
                    assert(len(subdir)==1)
                    build_root = p_tmp_dir/subdir[0]

                    logging.debug(f_tmp.name)
                    logging.info("compile")

                    logging.debug("cmake")
                    assert(subprocess.run(shell=True, args="cmake .", cwd=build_root).returncode==0)
                    logging.debug("make solc")
                    assert(subprocess.run(shell=True, args="make solc", cwd=build_root).returncode == 0)
                    solc_binary = build_root / "solc" / "solc"
                    assert(solc_binary.is_file())
                    logging.debug("SOLC_IS_FILE!!!")
                    logging.debug(tmp_dir)
                    logging.info("installing binary %s to %s"%(solc_binary, self._solc_directory / ("solc-%s" % version)))
                    shutil.move(src=str(solc_binary), dst=str(self._solc_directory / ("solc-%s" % version)))
            elif _type == ESolcType.static_linux:
                solc_binary = Path(f_tmp.name)
                logging.info("installing binary %s to %s" % (solc_binary, self._solc_directory / ("solc-%s" % version)))
                shutil.copy(src=str(solc_binary), dst=str(self._solc_directory / ("solc-%s" % version)))
                os.chmod(str(self._solc_directory / ("solc-%s" % version)), 0o744)
        logging.info("install completed.")

    def uninstall(self, version):
        if not version:
            raise Exception("version cannot be empty. wildcards are supported though.")
        for v, path in self.list(version=version):
            logging.info ("uninstall %s"%path)
            #os.unlink(path)  # todo enable

    @staticmethod
    def download_file(url, f_destination):
        response = requests.get(url, stream=True)
        for chunk in response.iter_content(chunk_size=1024*1024):
            if chunk:
                f_destination.write(chunk)
                f_destination.flush()
        f_destination.seek(0)
        return f_destination

    def run(self, version=None, _type=ESolcType.source):
        # fork and execute as solc binary
        path = self.list(version=version)
        if not path:
            # version not installed, download, build and install it.
            self.install(version=version, _type=_type)
            path = self.list(version=version).values()[0]
        elif len(path)==1:
            # pop the result
            path = list(path.values())[0]
        else:
            # take the latest version
            path = self.list_sorted()[0][1]

        os.execve(path=str(path), argv=[str(path)] + self._solc_args, env=os.environ.copy())

    def autodetect(self, solidity_file):
        # read pragma line
        # todo: implement?
        raise NotImplementedError("not implmented")
        header = None
        with open(solidity_file, 'r') as f:
            for line in f:
                if line.startswith("pragma solidity "):
                    break
        # regex pragma line
        #todo

    def parse_args(self, args):
        multisolc_args = {"x-from-source": None, "x-from-static": None, "x-version": None, "x-list":None}
        solc_args = []

        for i, a in enumerate(args):
            arg_key = a.lstrip("--")
            if any(arg_key.startswith(w) for w in multisolc_args.keys()):
                if "=" in arg_key:
                    k,v = arg_key.split("=",1)
                    multisolc_args[k] = v.strip()
                else:
                    multisolc_args[arg_key] = True
            else:
                if i==0:
                    continue  # skip first arg (image)
                solc_args.append(a)

        return multisolc_args, solc_args

def usage(msg=""):
    description = """
SOLCWrapper

Options:
    --x-list=<version>
    --x-version=<version>
    --x-from-source
    --x-from-static

Usage:
    #> python3 -m solcwrapper --x-list
    #> python3 -m solcwrapper --x-list=0.5.0
    #> python3 -m solcwrapper --x-version=0.5.1 <solc options and args>

    %s
""" % msg
    print(description)
    return 1

def main():
    # a default main
    ms = SolcWrapper(argv=sys.argv)

    if ms.args.get("x-list"):
        print("%-10s | %s"%("version","location"))
        print("----------------------")
        for v_path in ms.list(version=None if ms.args.get("x-list") is True else ms.args.get("x-list")).items():
            print("%-10s | %s" %v_path)
        return(0)

    if "--help" in sys.argv:
        usage()

    if ms.args.get("x-from-source"):
        _type = ESolcType.source
    elif ms.args.get("x-from-static"):
        _type = ESolcType.static_linux
    else:
        #default
        _type = ESolcType.source

    ms.run(version=ms.args.get("x-version"), _type=_type)


if __name__ == "__main__":
    sys.exit(main())
