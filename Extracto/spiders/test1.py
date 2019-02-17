# -*- coding: utf-8 -*-
import scrapy
from Extracto.items import ExtractoItem
import re

class Test1Spider(scrapy.Spider):
	name = 'test1'
	allowed_domains = ['amazon.com']

	categories, urls = [], []
	index, next_page_count, review_page_count = 0,0,0

	start_urls = ['https://www.amazon.com/s/browse/ref=nav_shopall-export_nav_mw_sbd_intl_electronics?_encoding=UTF8&node=16225009011']

	def parse(self, response):
		if response.css('title::text').extract_first() == 'International Shopping: Shop Electronics that Ship Internationally':
			divs = response.css('div.acs_tile__content')
			if not self.categories:
				for div in divs:
					url = div.css('a::attr(href)').extract_first()
					self.categories.append(div.css('span::text').extract_first().strip('\n').strip('\t').strip('\n'))
					self.urls.append(response.urljoin(url))
			
			yield scrapy.Request(self.urls[self.index], callback = self.parse_category)

	def parse_category(self, response):	

		detail_link = response.css('a.s-access-detail-page::attr(href)').extract()
		for link in detail_link:
			link = response.urljoin(link)
			request = scrapy.Request(link, callback = self.parse_item)
			request.meta['category'] = self.categories[self.index]
			yield request
					
		next_page_link = response.css('a#pagnNextLink::attr(href)').extract_first()
		if self.next_page_count < 3 and next_page_link:
			self.next_page_count += 1
			next_page_link = response.urljoin(next_page_link)
			yield scrapy.Request(next_page_link, callback = self.parse_category)
		else:
			self.index += 1
			self.next_page_count = 0
			if self.index < len(self.urls):
				yield scrapy.Request(self.urls[self.index], callback = self.parse_category)		

	def parse_item(self, response):	
		item = ExtractoItem()
		try:
			name = response.css('span#productTitle::text').extract_first().strip('\n ')
			price = response.css('span#priceblock_ourprice::text').extract_first()
			if name == None or price == None or ' ' in price:
				raise Exception
		except:
			return None		
		
		else:
			item['name'] = name
			item['price'] = ''
			for fragment in price.strip('$').split(','):
				item['price'] = item['price'] + fragment.strip(',')
			item['price'] = float(item['price'])	
		
		item['category'] = response.meta['category']		

		no_of_reviews = response.css('span#acrCustomerReviewText::text').extract_first()
		item['no_of_reviews'] = 0 if no_of_reviews==None else no_of_reviews.strip(' customer reviews')

		ratings = response.css('i.a-icon-star span.a-icon-alt::text').extract_first()
		item['ratings'] = None if ratings==None else float(ratings.split(' ')[0])
	
		#for image	
		item['image_urls'] = response.css('div#imgTagWrapperId img::attr(src)').extract_first().strip('\n') 				
		
		#for descriptions
		item['descriptions'] = []
		raw_descriptions = response.css('div#feature-bullets ul.a-unordered-list li span.a-list-item::text').extract()
		if raw_descriptions:
			for desc in raw_descriptions:
				desc = desc.strip(' \n\t')
				if desc != '':
					item['descriptions'].append(desc)

		if response.css('div.a-section.review'):
			item['reviews'] = []
			request = scrapy.Request(response.url, callback=self.parse_reviews)
			request.meta['item'] = item
			yield request
		else:
			return item

	def parse_reviews(self, response):
		item = response.meta['item']

		divs = response.css('div.a-section.review')
		for div in divs:
			reviewed_by = div.css('span.a-profile-name::text').extract_first()		
			rating = div.css('span.a-icon-alt::text').extract_first().split(' ')[0]
			if re.search('Customer reviews', response.css('title::text').extract_first()):
				review = div.css('span.review-text::text').extract_first()
			else:
				review = div.css('div.a-expander-content::text').extract_first()
			item['reviews'].append({'reviewed_by': reviewed_by, 'rating': rating, 'review': review})
			
		if response.css('a.a-link-emphasis'):
			next_link = response.css('a.a-link-emphasis::attr(href)').extract_first()
		elif response.css('li.a-last a'):
			next_link = response.css('li.a-last a::attr(href)').extract_first()
		
		if next_link and self.review_page_count < 2:
			self.review_page_count += 1
			request = scrapy.Request(response.urljoin('next_link'), callback=self.parse_reviews)
			request['meta'] = item
			yield request
		else:
			self.review_page_count = 0
			return item	
