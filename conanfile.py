#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
from conans import ConanFile, CMake, tools

class VSomeIPConan(ConanFile):
    name = "vsomeip"
    version = "3.1.20.3"
    license = "https://github.com/maingig/vsomeip/blob/master/LICENSE"
    author = "https://github.com/maingig/vsomeip/blob/master/AUTHORS"
    url = "https://github.com/maingig/vsomeip.git"
    description = "An implementation of Scalable service-Oriented MiddlewarE over IP"
    topics = ("tcp", "C++", "networking")
    settings = "os", "compiler", "build_type", "arch"
    exports = "*"
    options = {
        "shared": [ True, False ],
        "fPIC": [ True, False ],
    }
    default_options = {
        'shared': True,
        'fPIC': True,
        'boost:shared': False,
        'boost:without_context': True,
        'boost:without_coroutine': True,
        'boost:without_mpi': True,
    }
    generators = "cmake_find_package"

    # Custom variables
    source_url = url
    source_branch = "master"

    def requirements(self):
        self.requires("boost/1.73.0@%s/%s" % (self.user, self.channel))
        if self.settings.os != "Android":
            self.requires("gtest/[>=1.8]@%s/%s" % (self.user, self.channel))

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx

    def source(self):
        self.run("git clone %s %s" % (self.source_url, self.name))
        self.run("cd %s && git checkout tags/%s" % (self.name, self.version))
        """Wrap the original CMake file to call conan_basic_setup
        """
        shutil.move("%s/CMakeLists.txt" % (self.name), "%s/CMakeListsOriginal.txt" % (self.name))
        f = open("%s/CMakeLists.txt" % (self.name), "w")
        f.write('cmake_minimum_required(VERSION 2.8)\n')
        f.write('macro(ndk_find_package_boost)\n')
        f.write('    find_package( Boost 1.55 COMPONENTS ${ARGV} REQUIRED )\n')
        f.write('endmacro()\n')
        f.write('set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${CONAN_CXX_FLAGS}")\n')
        f.write('set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${CONAN_C_FLAGS}")\n')
        f.write('set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} ${CONAN_SHARED_LINKER_FLAGS}")\n')
        f.write('include(${CMAKE_SOURCE_DIR}/CMakeListsOriginal.txt)\n')
        f.close()

    def configure_cmake(self):
        cmake = CMake(self)
        if 'fPIC' in self.options and self.options.fPIC:
            cmake.definitions["CMAKE_C_FLAGS"] = "-fPIC"
            cmake.definitions["CMAKE_CXX_FLAGS"] = "-fPIC"
        if 'shared' in self.options:
            cmake.definitions["BUILD_SHARED_LIBS"] = self.options.shared
        if 'BASE_PATH' in self.env and len(self.env['BASE_PATH']) > 0:
            cmake.definitions["BASE_PATH"] = self.env['BASE_PATH']
        if 'ENABLE_SIGNAL_HANDLING' in self.env and len(self.env['ENABLE_SIGNAL_HANDLING']) > 0:
            cmake.definitions["ENABLE_SIGNAL_HANDLING"] = self.env['ENABLE_SIGNAL_HANDLING']
        if 'DIAGNOSIS_ADDRESS' in self.env and len(self.env['DIAGNOSIS_ADDRESS']) > 0:
            cmake.definitions["DIAGNOSIS_ADDRESS"] = self.env['DIAGNOSIS_ADDRESS']
        if 'UNICAST_ADDRESS' in self.env and len(self.env['UNICAST_ADDRESS']) > 0:
            cmake.definitions["UNICAST_ADDRESS"] = self.env['UNICAST_ADDRESS']
        if self.settings.os == "QNX":
            cmake.definitions["ENABLE_MULTIPLE_ROUTING_MANAGERS"] = 1
        cmake.definitions["VSOMEIP_INSTALL_ROUTINGMANAGERD"] = True
        cmake.configure(source_folder=self.name, build_folder=self.name)
        return cmake

    def build(self):
        cmake = self.configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self.name)
        cmake = self.configure_cmake()
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == "Windows":
            self.cpp_info.libs.extend(['winmm', 'ws2_32'])
        elif self.settings.os == "Linux":
            self.cpp_info.libs.extend(['pthread'])
        elif self.settings.os == "QNX":
            self.cpp_info.libs.extend(['socket'])
            self.cpp_info.defines.extend(["__EXT_BSD", "__QNXNTO__", "_QNX_SOURCE"])

