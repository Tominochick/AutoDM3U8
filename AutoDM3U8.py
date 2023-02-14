import platform
import sys
import os
import shutil
import time
from subprocess import Popen, TimeoutExpired, PIPE

sys_type = platform.system()
str_encoding = "utf-8"
N_m3u8DL_RE_path = ""
cmd_suffix = ""
main_pid = os.getpid()

Run_dir = os.getcwd()
Waiting_dir = os.path
Downloading_dir = os.path
Success_dir = os.path
Failure_dir = os.path
Result_dir = os.path


def mkdirsIfNotExist(*path: os.path):
    for p in path:
        if not os.path.exists(p):
            os.mkdir(p)


# print (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
with open("AutoDM3U8.pid", mode="w") as f:
    f.write(main_pid.__str__())
    print("MAIN process:" + main_pid.__str__() + " run in dir:" + Run_dir)
    Waiting_dir = os.path.join(Run_dir, "TASK-WAITING")
    Downloading_dir = os.path.join(Run_dir, "TASK-DOWNLOADING")
    Success_dir = os.path.join(Run_dir, "TASK-SUCCESS")
    Failure_dir = os.path.join(Run_dir, "TASK-FAILURE")
    Result_dir = os.path.join(Run_dir, "RESULT")
    mkdirsIfNotExist(Waiting_dir, Downloading_dir, Success_dir, Failure_dir, Result_dir)
if sys_type == "Windows":
    N_m3u8DL_RE_path = "N_m3u8DL-RE_Beta_win-x64\\N_m3u8DL-RE.exe "
    str_encoding = "gbk"
    cmd_suffix = ".bat"
elif sys_type == "Linux":
    N_m3u8DL_RE_path = "N_m3u8DL-RE_Beta_linux-x64/N_m3u8DL-RE "
    str_encoding = "utf-8"
    cmd_suffix = ".sh"
else:
    sys.stderr.write("nonsupport platform:" + sys_type + "\n")
    sys.exit(1)


def onSubmit(t_filename: str):
    t_file = os.path.join(Waiting_dir, t_filename)
    shutil.move(t_file, Downloading_dir)


def onFailure(t_filename: str):
    t_file = os.path.join(Downloading_dir, t_filename)
    if os.path.exists(t_file):
        shutil.move(t_file, Failure_dir)


def onSubmitFailure(t_filename: str):
    t_file = os.path.join(Waiting_dir, t_filename)
    if os.path.exists(t_file):
        shutil.move(t_file, Failure_dir)
    onFailure(t_filename)


def onSuccess(t_filename: str):
    t_file = os.path.join(Downloading_dir, t_filename)
    shutil.move(t_file, Success_dir)


def createTask(t_args: str, t_filename: str):
    t_args.replace("\n", " ")
    run_args = ""
    if t_args.find("N_m3u8DL-RE") == -1:
        run_args = N_m3u8DL_RE_path + t_args
    if t_args.find("--save-dir") == -1:
        run_args += " --save-dir " + Result_dir.__str__()
    if t_args.find("--save-name") == -1:
        run_args += ' --save-name "' + t_filename + "###" + time.strftime("%Y-%m-%d-%H:%M:%S", time.localtime()) + '"'

    with Popen(args=run_args, shell=True, encoding=str_encoding, stdout=PIPE) as proc:
        print("MAIN process:" + main_pid.__str__() + " run:" + run_args)
        onSubmit(t_filename)
        try:
            while True:
                buff = proc.stdout.readline()
                print("TASK process:" + proc.pid.__str__() + " " + buff, end="")
                if buff.find("ERROR") > -1:
                    print("TASK process:" + proc.pid.__str__() + " 失败")
                    onFailure(t_filename)
                    proc.kill()
                    return
                if buff.find("INFO") > -1 and buff.find("Done") > -1:
                    print("TASK process:" + proc.pid.__str__() + " 成功")
                    onSuccess(t_filename)
                    proc.kill()
                    return
                if buff == '' and proc.poll() is not None:
                    break

        except TimeoutExpired:
            proc.kill()
            onFailure(t_filename)


if __name__ == '__main__':
    MAX = 10  # 最多10个任务同时下载
    while True:
        if len(os.listdir(Downloading_dir)) == 10:
            pass
        files = os.listdir(Waiting_dir)
        for file in files:
            if file.endswith(cmd_suffix):
                task_file = os.path.join(Waiting_dir, file)
                try:
                    with open(task_file, mode="r", encoding="utf-8") as f:
                        args = f.read()
                    createTask(args, file)
                except Exception as e:
                    print(e)
                    onSubmitFailure(file)
            else:
                print("任务文件必须以" + cmd_suffix + "结尾")
                onSubmitFailure(file)
