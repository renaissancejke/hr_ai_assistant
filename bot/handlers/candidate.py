import os, datetime
from uuid import uuid4
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from settings.config import setup
from vacancies import VACANCIES
from bot.handlers.resume import process_resume

router = Router()


@router.message(CommandStart())
async def cmd_start(msg: types.Message, state: FSMContext):
    kb = [
        [types.InlineKeyboardButton(text=v, callback_data=f"vac|{v}")]
        for v in VACANCIES
    ]
    await msg.answer(
        "Привет! Выберите вакансию:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb),
    )
    await state.clear()


@router.callback_query(F.data.startswith("vac|"))
async def choose_vacancy(cb: types.CallbackQuery, state: FSMContext):
    vacancy = cb.data.split("|", 1)[1]
    await state.update_data(vacancy=vacancy)

    await cb.message.edit_text(
        f"Вы выбрали <b>{vacancy}</b>.\nПришлите файл *.txt* с резюме."
    )
    await cb.answer()


@router.message(F.document.mime_type == "text/plain")
async def handle_txt(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    if "vacancy" not in data:
        await msg.answer("Сначала выберите вакансию через /start.")
        return

    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    name = f"{ts}_{uuid4().hex}.txt"
    path = os.path.join(setup.data_dir, name)
    file_info = await msg.bot.get_file(msg.document.file_id)
    await msg.bot.download_file(file_info.file_path, destination=path)

    with open(path, encoding="utf-8", errors="ignore") as f:
        resume_txt = f.read()

    vacancy_name = data["vacancy"]
    vacancy_text = VACANCIES[vacancy_name]

    meta = await process_resume(
        file_path=path,
        resume_text=resume_txt,
        vacancy_name=vacancy_name,
        vacancy_text=vacancy_text,
        user_id=msg.from_user.id,
    )

    await msg.answer(
        "Спасибо! Ответим в течение недели.\n"
        "Подпишитесь на @rakestep, чтобы не пропустить новости."
    )

    caption = (
        f'{meta["tag"]} {meta["rating"]:.0f}% — <b>{vacancy_name}</b>\n'
        f'{meta["summary"]}\n'
        f'Советы: {meta["interview_tips"]}'
    )
    await msg.bot.send_document(
        setup.summary_chat_id,
        msg.document.file_id,
        caption=caption,
    )
