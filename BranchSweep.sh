#!/bin/bash
benchpairs=( "/home/software/simplesim/ss-benchmark/bzip2/bzip2_base.i386-m32-gcc42-nn /home/software/simplesim/ss-benchmark/bzip2/dryer.jpg" "/home/software/simplesim/ss-benchmark/mcf/mcf_base.i386-m32-gcc42-nn /home/software/simplesim/ss-benchmark/mcf/inp.in" "/home/software/simplesim/ss-benchmark/hmmer/hmmer_base.i386-m32-gcc42-nn /home/software/simplesim/ss-benchmark/hmmer/bombesin.hmm" "/home/software/simplesim/ss-benchmark/sjeng/sjeng_base.i386-m32-gcc42-nn /home/software/simplesim/ss-benchmark/sjeng/test.txt" "/home/software/simplesim/ss-benchmark/milc/milc_base.i386-m32-gcc42-nn < /home/software/simplesim/ss-benchmark/milc/su3imp.in")


branchsettings=( "-bpred perfect" "-bpred nottaken" "-bpred bimod -bpred:bimod 2048" "-bpred 2lev -bpred:2lev 1 1024 8 0" "-bpred 2lev -bpred:2lev 4 256 8 0" "-bpred comb -bpred:comb 1024" )

for benchnum in $(seq 0 $((${#benchpairs[*]} - 1))) ; do
   for branchnum in $(seq 0 $((${#branchsettings[*]} -1))); do 
       eval /home/software/simplescalar/x86_64/bin/sim-outorder -fastfwd 500000 -max:inst 2000000 -fetch:ifqsize 1 -fetch:speed 1 -fetch:mplat 3 -decode:width 1 -issue:width 1 -issue:inorder true -issue:wrongpath false -ruu:size 16 -lsq:size 8 -res:ialu 1 -res:imult 1 -res:memport 2 -res:fpalu 1 -res:fpmult 1 -cache:dl1lat 1 -cache:il1lat 1 -cache:dl2lat 6 -cache:il2lat 6 -mem:lat 58 6 -mem:width 8 -tlb:lat 30 ${branchsettings[$branchnum]} -redir:sim "$benchnum"-"$branchnum".inorder.simout ${benchpairs[$benchnum]}
       eval /home/software/simplescalar/x86_64/bin/sim-outorder -fastfwd 500000 -max:inst 2000000 -fetch:ifqsize 4 -fetch:speed 1 -fetch:mplat 5 -decode:width 4 -issue:width 4 -issue:inorder false -issue:wrongpath true -ruu:size 32 -lsq:size 8 -res:ialu 4 -res:imult 2 -res:memport 2 -res:fpalu 4 -res:fpmult 1 -cache:dl1lat 1 -cache:il1lat 1 -cache:dl2lat 6 -cache:il2lat 6 -mem:lat 58 6 -mem:width 8 -tlb:lat 30 ${branchsettings[$branchnum]} -redir:sim "$benchnum"-"$branchnum".outorder.simout ${benchpairs[$benchnum]}
   done
done

