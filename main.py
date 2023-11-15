import telebot
import buttons
import Database
from telebot import types

bot = telebot.TeleBot('6806552903:AAH-9X7rwHT8flbi01Kr7a0PDtNEdgNYkE4')

users = {}

# database.add_product('apple', 12000, 10, 'Apple the best', 'data:https://post.medicalnewstoday.com/wp-content/uploads/sites/3/2022/07/what_to_know_apples_green_red_1296x728_header-1024x575.jpg)

@bot.message_handler(commands=['start'])
def start_message(message):
    #Получаем тг ид
    user_id = message.from_user.id
    #Проверка пользователя
    checker = Database.check_user(user_id)

    #Если пользователь есть в базе
    if checker:
        # Получаем актуальный список продуктов
        products = Database.get_pr_name_id()
        print(products)

        #Отправим сообщение с меню
        bot.send_message(user_id, 'Привет')
        bot.send_message(user_id, 'Выберите пункт меню', reply_markup=buttons.main_menu(products))

    #Если пользователя нету в базе
    elif not checker:
        bot.send_message(user_id, 'Привет отправьте свое имя')

        # Переход на этап получения имени
        bot.register_next_step_handler(message, get_name)


#Получение имени
def get_name(message):
    user_id = message.from_user.id

    #Сохранить имя в переменную
    username = message.text

    #Отправим ответ
    bot.send_message(user_id, 'Отправьте свой номер телефона', reply_markup=buttons.number_buttons())
    #Направление на этап получения номера
    bot.register_next_step_handler(message, get_number, username)


#Получаем номер пользователя
def get_number(message, name):
    user_id = message.from_user.id

    if message.contact:
        #Сохраняем контакт
        phone_number = message.contact.phone_number

        #Сохраняем его в базе
        Database.register_user(user_id, name, phone_number, 'Not yet')
        bot.send_message(user_id, f'Вы успешно зарегистрировались {name}',
                         reply_markup=telebot.types.ReplyKeyboardRemove())

        #Открываем меню
        products = Database.get_pr_name_id()
        bot.send_message(user_id, 'Выберите пункт меню', reply_markup=buttons.main_menu(products))

    #Если пользователь не отправил контакт
    elif not message.contact:
        bot.send_message(user_id, 'Отправьте контакт с помощью кнопки', reply_markup=buttons.number_buttons())

        #Снова на этап получения номера
        bot.register_next_step_handler(message, get_number, name)

#Обработчик выбора количества
@bot.callback_query_handler(lambda call: call.data in ['plus', 'minus', 'to_cart', 'back'])
def get_user_product_count(call):
    #Сохраним айди пользователя
    user_id = call.message.chat.id

    #Если пользователь нажал на +
    if call.data == 'plus':
        print(users)
        actual_count = users[user_id]['pr_count']
        print(actual_count)
        print(call)
        users[user_id]['pr_count'] += 1
        #Меняем значение кнопки
        bot.edit_message_reply_markup(chat_id=user_id,
                                      message_id=call.message.message_id,
                                      reply_markup=buttons.choose_product_count('plus', actual_count))

    #Если пользователь нажал на -
    elif call.data == 'minus':
        print(users)
        actual_count = users[user_id]['pr_count']
        print(actual_count)
        print(call)
        users[user_id]['pr_count'] -= 1
        #Меняем значение кнопки
        bot.edit_message_reply_markup(chat_id=user_id,
                                      message_id=call.message.message_id,
                                      reply_markup=buttons.choose_product_count('minus', actual_count))

    #Если пользователь нажал 'назад'
    elif call.data == 'back':
        #Получаем меню
        products = Database.get_pr_name_id()
        #Меняем на меню
        bot.edit_message_text('Выберите пункт меню',
                              user_id,
                              call.message.message_id,
                              reply_markup=buttons.main_menu(products))

    #Если нажал добавить в корзину
    elif call.data == 'to_cart':
        #Получаем данные
        product_count = users[user_id]['pr_count']
        user_product = users[user_id]['pr_name']
        print(users)
        #Добавляем в базу cart
        Database.add_product_to_cart(user_id, user_product, product_count)

        #Получаем обратно меню
        products = Database.get_pr_name_id()
        #Меняем на меню
        bot.edit_message_text('Продукт добавлен в корзину\nЧто-нибудь еще?',
                              user_id,
                              call.message.message_id,
                              reply_markup=buttons.main_menu(products))



@bot.callback_query_handler(lambda call: call.data in ['order', 'cart', 'clear_cart'])
def main_menu_handle(call):
    user_id = call.message.chat.id
    message_id = call.message.message_id

    #Если нажал на кнопку: оформить заказ
    if call.data == 'order':
        # Удалим сообщение с верхними кнопками
        bot.delete_message(user_id, message_id)
        user_cart = Database.get_exact_user_cart(user_id)

        #Делаем сообщение со всей инфой
        full_text = 'Ваш заказ:\n\n'
        user_info = Database.get_user_number_name(user_id)
        print(user_info)
        full_text += f'Имя: {user_info[0]}\nНомер телефона: {user_info[1]}\n\n'
        total_amount = 0

        for i in user_cart:
            full_text += f'{i[0]} x {i[1]} = {i[2]}\n'
            total_amount += i[2]

        #Итон и адрес
        full_text += f'\nИтог: {total_amount}'

        bot.send_message(user_id, full_text, reply_markup=buttons.get_accept_kb())
        #Переход на этап подтверждение
        bot.register_next_step_handler(call.message, get_accept,  full_text)

    #Если нажал на кнопку "Корзина"
    elif call.data == 'cart':
        #Получим корзину пользователя
        user_cart = Database.get_exact_user_cart(user_id)

        #Формируем сообщение со всеми данными
        full_text = 'Ваша корзина:\n\n'
        total_amount = 0

        for i in user_cart:
            full_text += f'{i[0]} x {i[1]} = {i[2]}\n'
            total_amount += i[2]

        #Итог
        full_text += f'\nИтог: {total_amount}'

        #Отправляем ответ пользователю
        bot.edit_message_text(full_text,
                              user_id,
                              message_id,
                              reply_markup=buttons.get_cart())

    #Если нажал на очистить корзину
    elif call.data == 'clear_cart':
        #Вызов функции очистки корзины
        Database.delete_product_from_cart(user_id)

        #Отправим ответ
        bot.edit_message_text('Ваша корзина очищена',
                              user_id,
                              message_id,
                              reply_markup=buttons.main_menu(Database.get_pr_name_id()))



#Функция сохранения статуса заказа
def get_accept(message, full_text):
    user_id = message.from_user.id
    user_answer = message.text

    #Получим все продукты из базы для кнопок
    products = Database.get_pr_name_id()

    #Если пользователь нажал "подтвердить"
    if user_answer == 'Подтвердить':
        admin_id = 302137006
        #Очистить корзину пользователя
        Database.delete_product_from_cart(user_id)

        #Отправим адмэну сообщение о новом заказе
        bot.send_message(admin_id, full_text.replace("Ваш", "Новый"))

        #Отправим ответ
        bot.send_message(user_id, 'Заказ оформлен', reply_markup=types.ReplyKeyboardRemove())

    elif user_answer == 'Отменить':
        #Отправим ответ если отменить
        bot.send_message(user_id, 'Заказ отменен', reply_markup=types.ReplyKeyboardRemove())

    #Обратно в меню
    bot.send_message(user_id, 'Меню', reply_markup=buttons.main_menu(products))




#Обработчик выбора товара
@bot.callback_query_handler(lambda call: int(call.data) in Database.get_pr_id())
def get_user_product(call):
    #Сохраняем айди пользователя
    user_id = call.message.chat.id

    #Сохраняем продукт во временный словарь
    users[user_id] = {'pr_name': call.data, 'pr_count': 1}
    print(users)

    #Сохраняем айди сообщения
    message_id = call.message.message_id

    #Меняем кнопки на выбор кол-ва
    bot.edit_message_text('Выберите количество',
                          chat_id=user_id, message_id=message_id,
                          reply_markup=buttons.choose_product_count())

bot.infinity_polling()