from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, RadioField, SelectField, SelectMultipleField, FloatField, IntegerField, FileField
from wtforms.validators import ValidationError, DataRequired, Length
from flask_wtf.file import FileField, FileAllowed, FileRequired


class NewProjectForm( FlaskForm ):
    projectID = StringField('Project ID', validators=[
        DataRequired(), Length(min=1, max=140)])
    project_description = TextAreaField('Project Description', validators=[Length(min=1, max=280)])
    project_assembly = SelectField('Project Assembly', choices=[('hg19','hg19')], validators=[DataRequired()])
    project_DX = StringField('Project Main Diagnosis', validators=[DataRequired(), Length(min=1, max=140)])
    project_ICDS10 = StringField('Project Main Diagnosis ICD-10 code', validators=[DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('Submit')

consequence_choices = ([
    ( '1', '5_prime_UTR_variant (MODIFIER)' ),
    ( '2', '3_prime_UTR_variant (MODIFIER)' ),
    ( '3', 'downstream_gene_variant (MODIFIER)' ),
    ( '4', 'intron_variant (MODIFIER)' ),
    ( '5', 'intergenic_variant (MODIFIER)' ),
    ( '6', 'mature_miRNA_variant (MODIFIER)' ),
    ( '7', 'non_coding_transcript_exon_variant (MODIFIER)' ),
    ( '8', 'NMD_transcript_variant (MODIFIER)' ),
    ( '9', 'non_coding_transcript_variant (MODIFIER)' ),
    ( '10', 'upstream_gene_variant (MODIFIER)' ),
    ( '11', 'TFBS_ablation (MODIFIER)' ),
    ( '12', 'TFBS_amplification (MODIFIER)' ),
    ( '13', 'TF_binding_site_variant (MODIFIER)' ),
    ( '14', 'regulatory_region_ablation (MODERATE)' ),
    ( '15', 'regulatory_region_amplification (MODIFIER)' ),
    ( '16', 'feature_elongation (MODIFIER)' ),
    ( '17', 'regulatory_region_variant (MODIFIER)' ),
    ( '18', 'feature_truncation (MODIFIER)' ),
    ( '19', 'splice_region_variant (LOW)' ),
    ( '20', 'incomplete_terminal_codon_variant (LOW)' ),
    ( '21', 'start_retained_variant (LOW)' ),
    ( '22', 'stop_retained_variant (LOW)' ),
    ( '23', 'synonymous_variant (LOW)' ),
    ( '24', 'coding_sequence_variant (MODIFIER)' ),
    ( '25', 'inframe_insertion (MODERATE)' ),
    ( '26', 'inframe_deletion (MODERATE)' ),
    ( '27', 'missense_variant (MODERATE)' ),
    ( '28', 'protein_altering_variant (MODERATE)' ),
    ( '29', 'transcript_ablation (HIGH)' ),
    ( '30', 'transcript_amplification (HIGH)' ),
    ( '31', 'start_lost (HIGH)' ),
    ( '32', 'stop_lost (HIGH)' ),
    ( '33', 'frameshift_variant (HIGH)' ),
    ( '34', 'stop_gained (HIGH)' ),
    ( '35', 'splice_donor_variant (HIGH)' ),
    ( '36', 'splice_acceptor_variant (HIGH)' )
])

class FilterForm( FlaskForm ):
    filter_AF = FloatField('popmax AF', validators=[DataRequired()])
    filter_AC = IntegerField('max AC', validators=[DataRequired()])
    filter_GENELIST = FileField('genelist', validators=[
                                    FileRequired(),
                                    FileAllowed(['txt', 'gl'], 'TXT only!')
                                    ])
    filter_consequence = SelectMultipleField('Consequence to EXCLUDE', choices=consequence_choices, validators=[DataRequired()])

class SearchForm(FlaskForm):
    q = StringField('Search Variant', validators=[DataRequired()])
    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super(SearchForm, self).__init__(*args, **kwargs)
