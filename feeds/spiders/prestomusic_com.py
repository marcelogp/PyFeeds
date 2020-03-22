import scrapy

from scrapy import Selector
from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class PrestoMusicSpider(FeedsSpider):
    name = "prestomusic.com"
    start_urls = ["https://www.prestomusic.com/classical/formats/download/browse?date_range=Last+90+Days&sort=date&view=small&page=1&size=60"]

    feed_title = "Presto Classical"
    feed_subtitle = "Downloads, Last 90 Days"
    feed_link = "https://{}".format(name)
    feed_logo = "https://{}/favicon.ico".format(name)

    def parse(self, response):
        if '/browse' in response.url or '/search' in response.url:
            return self.parse_album_list(response)
        elif '/products' in response.url:
            return self.parse_album(response)
        else:
            self.log('Unexpected page %s' % response.url)

    def parse_album_list(self, response):
        albums = response.xpath('//div[contains(@class, "o-grid__item")]')

        for album in albums:
            sel = Selector(text=album.extract())
            album_href = sel.xpath('//a[contains(@class,"o-image")]/@href').extract_first()
            album_url = response.urljoin(album_href)

            yield scrapy.Request(album_url, self.parse_album)

    def parse_album(self, response):
        def _replace_track_info(elem):
            parts = list(map(lambda x: x.text_content().strip(), elem.getchildren()))
            return '<p>{} <i>({})</i></p>'.format(parts[0], parts[1])

        title = response.xpath('//h1[@class="c-product-block__title"]//text()').extract()[-1].strip()
        artist = response.xpath('//div[contains(@class,"c-product-block__contributors")]/p/text()').re_first('[^,]+')
        il = FeedEntryItemLoader(
            response=response,
            base_url="https://{}/".format(self.name),
            remove_elems=[
                '.c-product-block__title',
                '.c-product__product-purchase',
                '.c-track__format-specific-info',
                '.c-track__duration',
                '.c-track__details',
                '.c-tracklist__initial-tracks',
                '.c-tabs-block__tabs-links',
                'button'
            ],
            replace_elems={
                '.c-track__all-format-info': _replace_track_info
            }
        )
        il.add_value("title", '{} - {}'.format(artist, title))
        il.add_value("link", response.url)
        il.add_value("author_name", 'bot')
        il.add_css("content_html", 'div.c-page--product')
        return il.load_item()
