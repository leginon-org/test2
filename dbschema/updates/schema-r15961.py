#!/usr/bin/env python
from . import baseSchemaClass

class SchemaUpdate15961(baseSchemaClass.SchemaUpdate):
	'''
	This will add badAlign field to old apProtomoRefinementParamsData
	'''

	def upgradeAppionDB(self):
		if not self.appion_dbupgrade.columnExists('ApTomoAlignmentRunData', 'badAlign'):
			self.appion_dbupgrade.addColumn('ApTomoAlignmentRunData', 'badAlign', self.appion_dbupgrade.bool)

if __name__ == "__main__":
	update = SchemaUpdate15961()
	# update only leginon database
	update.setRequiredUpgrade('appion')
	update.run()

