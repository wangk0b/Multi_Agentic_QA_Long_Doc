sleep infinity
apt-get install sudo
wget https://aka.ms/downloadazcopy-v10-linux
tar -xvf downloadazcopy-v10-linux
cd azcopy_linux_amd64_*/
sudo mv ./azcopy /usr/local/bin/
sudo chmod +x /usr/local/bin/azcopy

azcopy cp "https://multimodel.blob.core.windows.net/docunderstanding/train_data/du_fv3_qwen_format.json?sp=racwdli&st=2025-06-16T09:05:44Z&se=2026-06-16T17:05:44Z&sv=2024-11-04&sr=c&sig=GC2vAl6qK2mgj0qz0vhzp%2BiP7PPFhsJVPbIDUwdrLnQ%3D" /tmp --recursive