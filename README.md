# ONLINE-ONLY TUTORIAL

## this is intended to give any registered user the chance to try Diagnosticator before deploy it locally

### adapt VCF names
# CASES to keep:
#   GHARALPI17uuC19341: COL4A5
#   GHARCAKUTI17uuC11551: PKD1 + TTC37 (het in AR)
#   GHARCKDI16uuC14491: COL4A5
#   GHARDMI17uuT16451: BRCA2
#   GHARCKDI17uuC19511: TP53
# CONTROLS to keep:
#   GHARCKDI16uuC17421: has a P in DHCR7 (het for AR)
#   GHARCKDI16uuF10851
#   GHARMALFI17uuM12111: has a LP in BBS5 (het for AR)
#   GHARFSGSI16uuC18301
#   GHARMNI16uuC10981
```
DIR=/home/enrico/columbia/diagnosticator-AWS/TUTORIAL-VCF/FILES/
VCF=${DIR}/2021-12-27_04-53-18_DX-TUTORIAL-MAF_0_variants.VEP-ANNOTATED.correct.vcf
# COLUMNS to keep (see above):
grep "^#" $VCF | tail -1 | tr '\t' '\n' | nl

grep "^#" $VCF | sed '$ d' > ${DIR}/HEADER-0.txt
grep "^#" $VCF | tail -1 | gawk -F'\t' -vOFS='\t' '{ print $1,$2,$3,$4,$5,$6,$7,$8,$9,"CASE-0","CASE-1","CASE-2","CASE-3","CASE-4","CONTROL-0","CONTROL-1","CONTROL-2","CONTROL-3","CONTROL-4" }' > ${DIR}/HEADER-1.txt
grep -v "^#" $VCF | gawk -F'\t' -vOFS='\t' '{ print $1,$2,$3,$4,$5,$6,$7,$8,$9,$16,$12,$26,$18,$17,$23,$20,$27,$22,$29 }' > ${DIR}/BODY.txt
cat ${DIR}/HEADER-0.txt ${DIR}/HEADER-1.txt ${DIR}/BODY.txt > ${DIR}/$( basename $VCF .vcf ).SEL.vcf
```

### before this you have to create the static file
#     as ex. created with a docker-compose version of the app
```
DXCATOR_DIR=$(pwd)
STATIC_FOLDER=/var/lib/docker/volumes/DX-ASILO-VOLUME/_data/analisi_result
# mkdir $DXCATOR_DIR/DB/ASILO_DIR
sudo cp -r $STATIC_FOLDER $DXCATOR_DIR/DB/ASILO_DIR/
sudo chown -R enrico:enrico $DXCATOR_DIR/DB/ASILO_DIR
```

### to create the static files from the analyzed ones
```
DXCATOR_DIR=$(pwd)
cd ${DXCATOR_DIR}
source venv/bin/activate

flask shell

from convert_VCF_REDIS import VCF2REDIS

ASILO_DIR = '/home/enrico/columbia/diagnosticator-AWS/diagnosticator-tutorial-on-server/DB/ASILO_DIR/analisi_result'

var_dict, sample_dict, gene_dict = VCF2REDIS( ASILO_DIR )

var_dict['X-107866056-G-C'].update({ 'KNOWN' : { 'P' : '1' } })

APP_DIR='/home/enrico/columbia/diagnosticator-AWS/diagnosticator-tutorial-on-server'

import json
import os
VAR_FILE=os.path.join( APP_DIR, 'JSON', 'var_dict.json' )
with open(VAR_FILE, 'w') as fp:
    json.dump(var_dict, fp)

SAMPLE_FILE=os.path.join( APP_DIR, 'JSON', 'sample_dict.json' )
with open( SAMPLE_FILE, 'w') as fp:
    json.dump(sample_dict, fp)

GENE_FILE=os.path.join( APP_DIR, 'JSON', 'gene_dict.json' )
with open(GENE_FILE, 'w') as fp:
    json.dump(gene_dict, fp)
```






























###ENDc
