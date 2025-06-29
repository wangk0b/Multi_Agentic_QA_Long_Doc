MAX_JOBS=40
for file in /tmp/Education/*
do
for jpg in $file/*
 do
  python qa_allam_vision.py --dir $jpg &
  
 while [ "$(jobs | wc -l)" -ge "$MAX_JOBS" ]; do
    sleep 1
  done
done
wait 
done 

for f in /eph/nvme0/azureml/cr/j/a9aea63d44994006b4c0cc85ffb5e334/exe/wd/*_QA
 do
  python concate.py --dir $f &
 done
