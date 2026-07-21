from alembic import op
import sqlalchemy as sa
revision="20260721_0002"; down_revision="20260721_01"; branch_labels=None; depends_on=None
def upgrade():
    with op.batch_alter_table("user_profile") as b:b.add_column(sa.Column("resume_text",sa.Text(),nullable=False,server_default=""))
    with op.batch_alter_table("companies") as b:
        b.add_column(sa.Column("intelligence_summary",sa.Text(),nullable=False,server_default="")); b.add_column(sa.Column("intelligence_json",sa.Text(),nullable=False,server_default="")); b.add_column(sa.Column("company_type",sa.String(120),nullable=False,server_default="")); b.add_column(sa.Column("estimated_size",sa.String(80),nullable=False,server_default="")); b.add_column(sa.Column("hiring_probability",sa.Integer(),nullable=False,server_default="0")); b.add_column(sa.Column("engineering_maturity",sa.Integer(),nullable=False,server_default="0")); b.add_column(sa.Column("outreach_probability",sa.Integer(),nullable=False,server_default="0")); b.add_column(sa.Column("risk_level",sa.String(30),nullable=False,server_default="Low"))
    with op.batch_alter_table("jobs") as b:b.add_column(sa.Column("description",sa.Text(),nullable=False,server_default="")); b.add_column(sa.Column("match_details",sa.Text(),nullable=False,server_default=""))
def downgrade():
    with op.batch_alter_table("jobs") as b:b.drop_column("match_details"); b.drop_column("description")
    with op.batch_alter_table("companies") as b:
        for n in ["risk_level","outreach_probability","engineering_maturity","hiring_probability","estimated_size","company_type","intelligence_json","intelligence_summary"]:b.drop_column(n)
    with op.batch_alter_table("user_profile") as b:b.drop_column("resume_text")
