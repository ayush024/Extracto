# -*- coding: utf-8 -*-
from scrapy.exporters import JsonLinesItemExporter
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html


class ExtractoPipeline(object):
    def process_item(self, item, test2):
        if item.get('price'):
 	      	item['price'] = price.split('$')[1]
       		return item
        else:
  	     	raise DropItem("Missing price in %s" % item)
        
class PerCategoryExportPipeline(object):

	def open_spider(self, spider):
		self.category_to_exporter = {}

	def close_spider(self, spider):
		for exporter in self.category_to_exporter.values():
			exporter.finish_exporting()
			exporter.file.close()

	def divide_item(self, item):
		item_review = {'reviews': item['reviews'], 'review_category': item['category']}
		del(item['reviews'])

		return [item, item_review]

	def _exporter_for_item(self, item):
		if 'category' in item.keys():
			category = item['category']
		else:
			category = 'reviews_of_'+item['review_category']
		
		if category not in self.category_to_exporter:
			f = open(f'{category}.json', 'wb')
			exporter = JsonLinesItemExporter(f)
			exporter.start_exporting()
			self.category_to_exporter[category] = exporter
		
		return self.category_to_exporter[category]

	def export_divided_item(self, item, spider):
		exporter = self._exporter_for_item(item)
		exporter.export_item(item)	
		return item

	def process_item(self, item, spider):
		items = self.divide_item(item)

		for item in items:
			self.export_divided_item(item, spider)















