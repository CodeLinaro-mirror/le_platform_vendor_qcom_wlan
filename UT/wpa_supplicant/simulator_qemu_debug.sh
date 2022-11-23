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

# $1 is the support architecture of the QEMU. i.e. arm or aarch64
# $2 is the port number. i.e. 12345
# $3 is the support architecture of gdb-multiarch. i.e. arm,aarch64,riscv:rv64, riscv:rv32
# $4 is the QEMU_LIBRARY. i.e.the vairable QEMU_LIBRARY in the lanuch script of VCAST
# $5 is name of executable which is passed by VCAST automatically.

#Launch the qemu and hang it
if [ "$#" -lt "4" ] || [ "$#" -gt "5" ]; then
  echo "$0: Incorrect number of arguments!"
  exit 1
fi

if [ "$#" -eq "4" ] ; then
  qemu-$1 -g $2 $4 &
fi

if [ "$#" -eq "5" ] ; then
  qemu-$1 -L $4 -g $2 $5 &
fi

#Preset the commandfile for gdb
rm -f gdbcommand
echo "set arch $3" > gdbcommand
echo "set endian little" >> gdbcommand
if [ "$#" -eq "5" ] ; then
  echo "set solib-absolute-prefix $4" >> gdbcommand
fi
echo "target remote localhost:$2" >> gdbcommand
#echo "display /i $pc" >> gdbcommand
echo "b main" >>gdbcommand
echo "c" >> gdbcommand

#Launch the gdb
if [ "$#" -eq "4" ] ; then
  gdb-multiarch $4 -x gdbcommand
fi

if [ "$#" -eq "5" ] ; then
  gdb-multiarch $5 -x gdbcommand
fi


#ctrl +x+a to open gdbtui
