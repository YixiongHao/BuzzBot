import asyncio
import time

import chainlit as cl
from chainlit.element import Element
from search import File, natural_language_search


def _get_file_element(file_meta: File) -> Element:
    element_cls_by_ext = {
        ".pdf": cl.Pdf,
        ".txt": cl.Text,
        ".mp3": cl.Audio,
        ".jpg": cl.Image,
        ".jpeg": cl.Image,
        ".png": cl.Image,
        ".md": cl.Text,
    }

    element_cls = element_cls_by_ext.get(file_meta.extension)
    if element_cls is None:
        raise ValueError(f"Unsupported file extension: {file_meta.extension}")

    return element_cls(path=file_meta.path, name=file_meta.filename, display="side")


async def time_consuming_function(user_input: str) -> None:
    # Load the environment variables
    loop = asyncio.get_running_loop()
    results, file_metas = await loop.run_in_executor(
        None, natural_language_search, user_input
    )

    if len(results.files) == 0 and results.result_type == "search":
        await cl.Message(content="No results found.").send()
        return

    elements = [_get_file_element(file_metas[result]) for result in results.files]

    # Build message content
    if results.result_type == "search":
        message_content = "Here are the search results:\n\n"
    else:
        message_content = f"{results.answer}\n\nSources:\n\n"

    # Add metadata table
    message_content += "| File | Size | Created |\n|------|------|---------|\n"

    for file in results.files:
        file_meta = file_metas[file]
        size_mb = f"{file_meta.size / (1024 * 1024):.2f} MB"
        created_dt = time.strftime("%Y-%m-%d %H:%M", time.localtime(file_meta.created))
        message_content += f"| {file_meta.filename} | {size_mb} | {created_dt} |\n"

    await cl.Message(content=message_content, elements=elements).send()


@cl.on_chat_start
async def start():
    await cl.Message(content="Hello! How can I assist you today?").send()


@cl.on_message
async def main(message: cl.Message):
    # Start a loading status indicator
    async with cl.Step("search"):
        await time_consuming_function(message.content)


if __name__ == "__main__":
    cl.run()
