/*
 * Copyright (c) 2022 Qualcomm Innovation Center, Inc. All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted (subject to the limitations in the
 * disclaimer below) provided that the following conditions are met:
 *
 *   * Redistributions of source code must retain the above copyright
 *     notice, this list of conditions and the following disclaimer.
 *
 *   * Redistributions in binary form must reproduce the above
 *     copyright notice, this list of conditions and the following
 *     disclaimer in the documentation and/or other materials provided
 *     with the distribution.
 *
 *   * Neither the name of Qualcomm Innovation Center, Inc. nor the names of its
 *     contributors may be used to endorse or promote products derived
 *     from this software without specific prior written permission.
 *
 * NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE
 * GRANTED BY THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT
 * HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
 * WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
 * IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
 * ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
 * GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
 * IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
 * OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
 * IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

# set the correct License server and port to VECTOR_LICENSE_FILE
export VECTOR_LICENSE_FILE=port@ip_address

# path to where VectorCAST is installed
export VECTORCAST_DIR=/vcast

# path to where cross compiler is
export COMPILER_PATH=/poky/build/tmp-glibc/work/aarch64-oe-linux/wpa-supplicant/git-r5.2/recipe-sysroot-native/usr
export PATH=$COMPILER_PATH/bin/aarch64-oe-linux:$PATH

# the cross compiler executable name for C and C++
# VCAST_COMPILER_G++ is not used for the C project
#export VCAST_COMPILER_GCC=arm-eabi-gcc
#export VCAST_COMPILER_GPP=arm-eabi-g++
export VCAST_COMPILER_GCC=aarch64-oe-linux-gcc
export VCAST_COMPILER_GPP=aarch64-oe-linux-g++

# QEMU is the simulator to run the test
# QEMU_LIBRARY is the path to the compiler default library path
# QEMU_LIBRARY is varied with different compiler
#export QEMU_LIBRARY=$COMPILER_PATH/lib
export QEMU_LIBRARY=$COMPILER_PATH/../../recipe-sysroot

export QEMU_DEBUG_SCRIPT_PATH=$PWD/VectorCAST_CFG
export VCAST_DONT_EXTRACT_MACROS=
export SEARCH_PATH=/external/wpa_supplicant_8

# for the demonstration we are using a Raspberry PI compiler
# The compiler should already be in the path in Linux, if not set the path here
$VECTORCAST_DIR/vcastqt
