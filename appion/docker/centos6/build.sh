#!/bin/sh

wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/112/06jul12a_00015gr_00028sq_00004hl_00002en.mrc'
wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/113/06jul12a_00015gr_00028sq_00023hl_00002en.mrc'
wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/114/06jul12a_00015gr_00028sq_00023hl_00004en.mrc'
wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/115/06jul12a_00022gr_00013sq_00002hl_00004en.mrc'
wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/116/06jul12a_00022gr_00013sq_00003hl_00005en.mrc'
wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/109/06jul12a_00022gr_00037sq_00025hl_00004en.mrc'
wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/110/06jul12a_00022gr_00037sq_00025hl_00005en.mrc'
wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/111/06jul12a_00035gr_00063sq_00012hl_00004en.mrc'

docker build -t vosslab/appion .