import sys
import subprocess

def run_ssh_command(ip, password, command):
    print(f"Running command on {ip}...")
    ssh_cmd = [
        "sshpass", "-p", password,
        "ssh", "-o", "StrictHostKeyChecking=no", f"root@{ip}",
        command
    ]
    res = subprocess.run(ssh_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error on {ip}: {res.stderr}")
        return False
    else:
        print(f"Success on {ip}: {res.stdout.strip()}")
        return True

servers = [
    {"ip": "213.171.9.62", "pass": "nDrv1u?KGA9e#R", "name": "Dev"},
    {"ip": "147.45.143.60", "pass": "kax5Pvkr,WXW5V", "name": "Production"}
]

menu_content = """<?
$aMenuLinks = Array(
	Array(
		"Мой кабинет",
		"personal/",
		Array(),
		Array(),
		""
	),


	Array(
		"Текущие заказы",
		"personal/orders/",
		Array(),
		Array(),
		""
	),

	Array(
		"Личный счет",
		"personal/account/",
		Array(), 
		Array(),
		"CBXFeatures::IsFeatureEnabled('SaleAccounts')"
	),

	Array(
		"Личные данные",
		"personal/private/",
		Array(), 
		Array(), 
		"" 
	),
	Array(
		"История заказов",
		"personal/orders/?filter_history=Y",
		Array(),
		Array(),
		""
	),
	Array(
		"Профили заказов",
		"personal/profiles/",
		Array(),
		Array(),
		""
	),
	Array(
		"Корзина",
		"/basket/",
		Array(),
		Array(),
		""
	),
	Array(
		"Подписки",
		"personal/subscribe/",
		Array(),
		Array(),
		""
	),
	Array(
		"Контакты",
		"about/contacts/",
		Array(),
		Array(),
		""
	),
);
?>"""

viewed_product_content = """<?if(!defined("B_PROLOG_INCLUDED") || B_PROLOG_INCLUDED!==true)die();?>
<?$APPLICATION->IncludeComponent("bitrix:catalog.viewed.products", "bootstrap_v4", array(
		"HIDE_NOT_AVAILABLE" => "N",
		"PAGE_ELEMENT_COUNT" => "5",
		"SHOW_DISCOUNT_PERCENT" => "Y",
		"PRODUCT_SUBSCRIPTION" => "N",
		"SHOW_NAME" => "Y",
		"SHOW_IMAGE" => "Y",
		"MESS_BTN_BUY" => "Купить",
		"MESS_BTN_DETAIL" => "Подробнее",
		"MESS_BTN_SUBSCRIBE" => "Подписаться",
		"LINE_ELEMENT_COUNT" => "5",
		"TEMPLATE_THEME" => "site",
		"SHOW_OLD_PRICE" => "N",
		"PRICE_CODE" => array(
			0 => "BASE",
		),
		"SHOW_PRICE_COUNT" => "1",
		"PRICE_VAT_INCLUDE" => "Y",
		"CONVERT_CURRENCY" => "N",
		"BASKET_URL" => "/basket/",
		"ACTION_VARIABLE" => "action_cvp",
		"PRODUCT_ID_VARIABLE" => "id",
		"ADD_PROPERTIES_TO_BASKET" => "Y",
		"PRODUCT_PROPS_VARIABLE" => "prop",
		"PARTIAL_PRODUCT_PROPERTIES" => "N",
		"USE_PRODUCT_QUANTITY" => "N",
		"SHOW_PRODUCTS_2" => "Y",
		"OFFER_TREE_PROPS_3" => array(
			0 => "COLOR_REF",
			1 => "SIZES_SHOES",
			2 => "SIZES_CLOTHES",
		),
		"PRODUCT_QUANTITY_VARIABLE" => "quantity",
		"CACHE_GROUPS" => "Y"
	),
	false
);?>"""

cart_redirect_content = """<?
require($_SERVER["DOCUMENT_ROOT"]."/bitrix/modules/main/include/prolog_before.php");
LocalRedirect("/basket/", true);
die();
?>"""

order_redirect_content = """<?
require($_SERVER["DOCUMENT_ROOT"]."/bitrix/modules/main/include/prolog_before.php");
LocalRedirect("/order/", true);
die();
?>"""

for server in servers:
    print(f"=== Configuring {server['name']} ({server['ip']}) ===")
    
    # Backup files first
    backup_command = (
        "cp /home/bitrix/ext_www/mhave.ru/.personal.menu.php /home/bitrix/ext_www/mhave.ru/.personal.menu.php.bak 2>/dev/null; "
        "cp /home/bitrix/ext_www/mhave.ru/include/viewed_product.php /home/bitrix/ext_www/mhave.ru/include/viewed_product.php.bak 2>/dev/null; "
        "cp /home/bitrix/ext_www/mhave.ru/personal/cart/index.php /home/bitrix/ext_www/mhave.ru/personal/cart/index.php.bak 2>/dev/null; "
        "cp /home/bitrix/ext_www/mhave.ru/personal/order/make/index.php /home/bitrix/ext_www/mhave.ru/personal/order/make/index.php.bak 2>/dev/null"
    )
    run_ssh_command(server['ip'], server['pass'], backup_command)
    
    # Write new content
    # 1. .personal.menu.php
    cmd_menu = f"cat << 'EOF' > /home/bitrix/ext_www/mhave.ru/.personal.menu.php\n{menu_content}\nEOF"
    run_ssh_command(server['ip'], server['pass'], cmd_menu)
    
    # 2. include/viewed_product.php
    cmd_viewed = f"cat << 'EOF' > /home/bitrix/ext_www/mhave.ru/include/viewed_product.php\n{viewed_product_content}\nEOF"
    run_ssh_command(server['ip'], server['pass'], cmd_viewed)
    
    # 3. personal/cart/index.php
    cmd_cart = f"cat << 'EOF' > /home/bitrix/ext_www/mhave.ru/personal/cart/index.php\n{cart_redirect_content}\nEOF"
    run_ssh_command(server['ip'], server['pass'], cmd_cart)
    
    # 4. personal/order/make/index.php
    cmd_order = f"cat << 'EOF' > /home/bitrix/ext_www/mhave.ru/personal/order/make/index.php\n{order_redirect_content}\nEOF"
    run_ssh_command(server['ip'], server['pass'], cmd_order)
    
    print(f"=== Done with {server['name']} ===\n")
