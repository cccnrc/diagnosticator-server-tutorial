import os
import tarfile
import docker

client = docker.from_env()

def copy_to_docker(src, dst):
    name, dst = dst.split(':')
    container = client.containers.get(name)

    os.chdir(os.path.dirname(src))
    srcname = os.path.basename(src)
    tar = tarfile.open(src + '.tar', mode='w')
    try:
        tar.add(srcname)
    finally:
        tar.close()

    data = open(src + '.tar', 'rb').read()
    container.put_archive(os.path.dirname(dst), data)

# file0 = '/home/enrico/columbia/diagnosticator-AWS/diagnosticator-local-simple-ALGORITHM-DEVELOPMENT-00/GHARRIVURY20_n93.snpEff_annotated.noAF.merged.splitted.NO-shift.VEP-annotated.head-50k.vcf'
# copy_to( file0, 'rq-worker:/home/diagnosticator/upload/')
